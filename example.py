class Pointr:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def print(self) -> None:
        print(self.x, self.y)

def main() -> None:
    p: Pointr = Pointr(3, 4)
    p.print()
