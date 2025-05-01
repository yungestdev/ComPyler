import ast

PYTHON_TO_C_TYPES = {
    'int': 'int',
    'float': 'double',
    'str': 'char*',
    'bool': 'int',
}

class Compiler(ast.NodeVisitor):
    def __init__(self):
        self.output = []
        self.indent_level = 0
        self.variables = {}  # var_name: c_type
        self.classes = {}    # class_name: list of (type, field)
        self.includes = {"#include <stdio.h>", "#include <stdlib.h>", "#include <string.h>"}

    def indent(self):
        return '    ' * self.indent_level

    def emit(self, line: str):
        """Emit a line with proper indentation and ensure newlines."""
        self.output.append(f"{self.indent()}{line}\n")

    def compile(self, source: str) -> str:
        tree = ast.parse(source)
        self.visit(tree)
        includes = "\n".join(sorted(self.includes))
        return f"{includes}\n\n{''.join(self.output)}"

    def resolve_type(self, annotation):
        if annotation is None:
            return 'int'  # Default return type
        elif isinstance(annotation, ast.Name):
            return {
                'int': 'int',
                'float': 'double',
                'str': 'char*',
                'bool': 'int',
                'None': 'void',
            }.get(annotation.id, f"struct {annotation.id}*")
        elif isinstance(annotation, ast.Constant) and annotation.value is None:
            return 'void'
        raise TypeError(f"Unsupported annotation: {ast.dump(annotation)}")

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_ClassDef(self, node):
        class_name = node.name
        fields = []
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == '__init__':
                for sub in stmt.body:
                    if isinstance(sub, ast.Assign) and isinstance(sub.targets[0], ast.Attribute):
                        attr = sub.targets[0].attr
                        typ = self.infer_type_from_value(sub.value)
                        fields.append((typ, attr))
        self.classes[class_name] = fields

        self.emit(f"struct {class_name} {{")
        self.indent_level += 1
        for typ, name in fields:
            self.emit(f"{typ} {name};")
        self.indent_level -= 1
        self.emit("};\n")

        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self.visit_method(stmt, class_name)

    def visit_method(self, node, class_name):
        args = []
        self.variables = {}

        for i, arg in enumerate(node.args.args):
            if i == 0:
                args.append(f"struct {class_name}* self")
                self.variables[arg.arg] = f"struct {class_name}*"
            else:
                if not arg.annotation:
                    raise Exception("All args must have annotations")
                ctype = self.resolve_type(arg.annotation)
                args.append(f"{ctype} {arg.arg}")
                self.variables[arg.arg] = ctype

        ret_type = self.resolve_type(node.returns)
        self.emit(f"{ret_type} {class_name}_{node.name}({', '.join(args)}) {{")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.emit("}\n")

    def visit_FunctionDef(self, node):
        args = []
        self.variables = {}
        for arg in node.args.args:
            if not arg.annotation:
                raise Exception(f"Argument {arg.arg} must be annotated")
            ctype = self.resolve_type(arg.annotation)
            self.variables[arg.arg] = ctype
            args.append(f"{ctype} {arg.arg}")

        ret_type = self.resolve_type(node.returns)
        self.emit(f"{ret_type} {node.name}({', '.join(args)}) {{")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.emit("}\n")

    def visit_AnnAssign(self, node):
        # Handle annotated assignments (e.g., p: Point = Point(...))
        if node.value is None:
            return
        target = node.target
        if isinstance(target, ast.Name):
            name = target.id
            val = self.visit(node.value)
            ctype = self.resolve_type(node.annotation)
            self.variables[name] = ctype
            self.emit(f"{ctype} {name} = {val};")
        elif isinstance(target, ast.Attribute):
            obj = self.visit(target.value)
            val = self.visit(node.value)
            self.emit(f"{obj}->{target.attr} = {val};")
        else:
            raise NotImplementedError(f"Unsupported AnnAssign target: {ast.dump(target)}")

    def visit_Return(self, node):
        self.emit(f"return {self.visit(node.value)};")

    def visit_Assign(self, node):
        target = node.targets[0]
        if isinstance(target, ast.Name):
            name = target.id
            value = self.visit(node.value)
            if name not in self.variables:
                ctype = self.infer_type_from_value(node.value)
                self.variables[name] = ctype
                self.emit(f"{ctype} {name} = {value};")
            else:
                self.emit(f"{name} = {value};")
        elif isinstance(target, ast.Attribute):
            self.emit(f"{self.visit(target.value)}->{target.attr} = {self.visit(node.value)};")

    def visit_Expr(self, node):
        self.emit(f"{self.visit(node.value)};")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id == 'print':
                fmt_parts = []
                arg_vals = []
                for arg in node.args:
                    val = self.visit(arg)
                    typ = self.get_expr_type(arg)
                    if typ == 'int': fmt_parts.append("%d")
                    elif typ in ('double','float'): fmt_parts.append("%f")
                    elif typ == 'char*': fmt_parts.append("%s")
                    else: fmt_parts.append("%p")
                    arg_vals.append(val)
                fmt_str = ' '.join(fmt_parts)
                return f'printf("{fmt_str}", {", ".join(arg_vals)})'
            elif node.func.id in self.classes:
                class_name = node.func.id
                args = [self.visit(a) for a in node.args]
                var = f"tmp_{class_name.lower()}"
                self.emit(f"struct {class_name}* {var} = malloc(sizeof(struct {class_name}));")
                self.emit(f"{class_name}___init__({var}, {', '.join(args)});")
                self.variables[var] = f"struct {class_name}*"
                return var
            else:
                return f"{node.func.id}({', '.join(self.visit(a) for a in node.args)})"
        elif isinstance(node.func, ast.Attribute):
            obj = self.visit(node.func.value)
            class_type = self.get_expr_type(node.func.value).replace("struct ","").replace("*","")
            args = [obj] + [self.visit(a) for a in node.args]
            return f"{class_type}_{node.func.attr}({', '.join(args)})"

    def visit_Attribute(self, node):
        return f"{self.visit(node.value)}->{node.attr}"

    def visit_Name(self, node):
        return node.id

    def visit_Constant(self, node):
        if isinstance(node.value, str): return f'"{node.value}"'
        if isinstance(node.value, bool): return "1" if node.value else "0"
        return str(node.value)

    def visit_BinOp(self, node):
        return f"({self.visit(node.left)} {self.get_op(node.op)} {self.visit(node.right)})"

    def get_op(self, op):
        return {
            ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
            ast.Mod: '%', ast.Pow: '^'
        }.get(type(op), '?')

    def get_expr_type(self, node):
        if isinstance(node, ast.Name): return self.variables.get(node.id, 'int')
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, int): return 'int'
            if isinstance(v, float): return 'double'
            if isinstance(v, str): return 'char*'
            if isinstance(v, bool): return 'int'
        if isinstance(node, ast.Attribute):
            owner = self.get_expr_type(node.value)
            if owner.startswith("struct ") and owner.endswith("*"):
                cls = owner[7:-1]
                for typ, field in self.classes.get(cls, []):
                    if field == node.attr: return typ
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self.classes:
                return f"struct {node.func.id}*"
            return 'int'
        return 'int'

    def infer_type_from_value(self, value):
        return self.get_expr_type(value)

if __name__ == "__main__":
    with open("example.py") as f:
        source = f.read()
    compiler = Compiler()
    output = compiler.compile(source)
    print(output)
    with open("out.c", "w") as f:
        f.write(output)
    print("[+] Compilation complete")
