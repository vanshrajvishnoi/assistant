# input/cursor.py
from pynput.mouse import Controller

mouse = Controller()

def get_cursor_position() -> tuple[int, int]:
    pos = mouse.position
    return int(pos[0]), int(pos[1])