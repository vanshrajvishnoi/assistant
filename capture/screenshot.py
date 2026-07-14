import mss
from PIL import Image, ImageDraw

from config import CURSOR_MARKER_COLOR, CURSOR_MARKER_RADIUS

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # older Pillow
    _RESAMPLE = Image.LANCZOS


def capture_full_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[0] 
        sct_img = sct.grab(monitor)
        image = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    origin = (monitor["left"], monitor["top"])
    size = (monitor["width"], monitor["height"])
    return image, origin, size


def prepare_for_upload(image: Image.Image, cursor_phys_xy, region_origin, max_dimension: int):
    width, height = image.size
    scale = min(1.0, max_dimension / max(width, height))
    resized = image.resize((int(width * scale), int(height * scale)), _RESAMPLE) if scale < 1.0 else image.copy()

    marker_x = int((cursor_phys_xy[0] - region_origin[0]) * scale)
    marker_y = int((cursor_phys_xy[1] - region_origin[1]) * scale)

    draw = ImageDraw.Draw(resized)
    r = CURSOR_MARKER_RADIUS
    draw.ellipse(
        [marker_x - r, marker_y - r, marker_x + r, marker_y + r],
        outline=CURSOR_MARKER_COLOR,
        width=3,
    )
    draw.line([marker_x - r * 2, marker_y, marker_x + r * 2, marker_y], fill=CURSOR_MARKER_COLOR, width=2)
    draw.line([marker_x, marker_y - r * 2, marker_x, marker_y + r * 2], fill=CURSOR_MARKER_COLOR, width=2)

    return resized