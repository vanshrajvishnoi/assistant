def bbox_to_screen(bbox, region_origin, region_size, dpr):
    if not bbox or len(bbox) != 4:
        return None

    ymin, xmin, ymax, xmax = bbox
    if not all(0 <= v <= 1000 for v in (ymin, xmin, ymax, xmax)):
        return None

    width, height = region_size
    cx_norm = (xmin + xmax) / 2 / 1000
    cy_norm = (ymin + ymax) / 2 / 1000

    phys_x = region_origin[0] + cx_norm * width
    phys_y = region_origin[1] + cy_norm * height

    logical_x = int(phys_x / dpr)
    logical_y = int(phys_y / dpr)
    return logical_x, logical_y