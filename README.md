
# ComPyler - Python to C Compiler

ComPyler is a **Python to C** compiler written in pure Python. This project aims to translate Python code into equivalent C code while preserving most Python features and types. The goal of this project is to create a fully dynamic compiler that can handle Python syntax, functions, classes, and various types without relying on third-party tools like `mypy`, `Cython`, or `LLVM`.

## Features

- **Python-to-C Translation:** Translates Python syntax and logic to equivalent C code.
- **Supports Python Classes:** Automatically handles Python classes and their fields, translating them into C structs.
- **Type Resolution:** Resolves Python types (`int`, `float`, `str`, `bool`) and generates corresponding C types.
- **Function Support:** Handles both regular Python functions and class methods, including type annotations.
- **Annotations for Variables and Functions:** Handles Python variable and function annotations for type inference and translation to C.
- **Memory Management:** Automatically manages dynamic memory allocation for objects (via `malloc`) where necessary.
- **C Standard Library Support:** Includes common C standard libraries (`stdio.h`, `stdlib.h`, `string.h`) for basic functionality like printing and memory management.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/ComPyler.git
    cd ComPyler
    ```

2. Ensure that Python 3.x is installed.

3. Install any dependencies (currently only `ast` module from Python standard library):

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Place your Python source code file (e.g., `example.py`) in the project directory.

2. Run the compiler:

    ```bash
    python compiler.py
    ```

3. The resulting C code will be saved to `out.c` and printed to the console.

4. You can now compile the generated C code using a C compiler, such as GCC:

    ```bash
    gcc -o out out.c
    ```

5. Run the compiled C program:

    ```bash
    ./out
    ```

## Example

### Python Source (example.py):

```python
class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

def main():
    p = Point(10, 20)
    p.move(5, -5)
    print(p.x, p.y)

if __name__ == "__main__":
    main()
```

### Generated C Code (out.c):

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Point {
    int x;
    int y;
};

void Point_move(struct Point* self, int dx, int dy) {
    self->x += dx;
    self->y += dy;
}

int main() {
    struct Point* p = malloc(sizeof(struct Point));
    Point___init__(p, 10, 20);
    Point_move(p, 5, -5);
    printf("%d %d
", p->x, p->y);
    return 0;
}
```

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Make your changes and commit them (`git commit -am 'Add feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
