from cityviz.utils import to_isometric, grid_to_world


def test_to_isometric():
    grid = [
        (0, 0), (1, 0), (2, 0),
        (0, 1), (1, 1), (2, 1),
        (0, 2), (1, 2), (2, 2)
    ]

    actual = [to_isometric(coord) for coord in grid]

    expected = [
        (0, 0), (64, 32), (128, 64),
        (-64, 32), (0, 64), (64, 96),
        (-128, 64), (-64, 96), (0, 128)
    ]

    assert expected == actual


def test_grid_to_world():
    grid = [
        (0, 0), (1, 0), (2, 0),
        (0, 1), (1, 1), (2, 1),
        (0, 2), (1, 2), (2, 2)
    ]

    results = [grid_to_world(coord) for coord in grid]

    actual_cart_rects = [res['cart_rect'] for res in results]

    expected_cart_rects = [
        # Rect for (0, 0)
        ((0, 0), (64, 0), (64, 64), (0, 64)),
        # Rect for (1, 0)
        ((64, 0), (128, 0), (128, 64), (64, 64)),
        # Rect for (2, 0)
        ((128, 0), (192, 0), (192, 64), (128, 64)),
        # Rect for (0, 1)
        ((0, 64), (64, 64), (64, 128), (0, 128)),
        # Rect for (1, 1)
        ((64, 64), (128, 64), (128, 128), (64, 128)),
        # Rect for (2, 1)
        ((128, 64), (192, 64), (192, 128), (128, 128)),
        # Rect for (0, 2)
        ((0, 128), (64, 128), (64, 192), (0, 192)),
        # Rect for (1, 2)
        ((64, 128), (128, 128), (128, 192), (64, 192)),
        # Rect for (2, 2)
        ((128, 128), (192, 128), (192, 192), (128, 192)),
    ]

    assert expected_cart_rects == actual_cart_rects

    actual_iso_polygons = [res['iso_poly'] for res in results]

    expected_iso_polygons = [
        # Iso Poly for (0, 0)
        ((0, 0), (32, 16), (0, 32), (-32, 16)),
        # Iso Poly for (1, 0)
        ((64, 0), (128, 0), (128, 64), (64, 64)),
        # Iso Poly for (2, 0)
        ((128, 0), (192, 0), (192, 64), (128, 64)),
        # Iso Poly for (0, 1)
        ((0, 64), (64, 64), (64, 128), (0, 128)),
        # Iso Poly for (1, 1)
        ((64, 64), (128, 64), (128, 128), (64, 128)),
        # Iso Poly for (2, 1)
        ((128, 64), (192, 64), (192, 128), (128, 128)),
        # Iso Poly for (0, 2)
        ((0, 128), (64, 128), (64, 192), (0, 192)),
        # Iso Poly for (1, 2)
        ((64, 128), (128, 128), (128, 192), (64, 192)),
        # Iso Poly for (2, 2)
        ((128, 128), (192, 128), (192, 192), (128, 192)),
    ]

    assert expected_iso_polygons[0] == actual_iso_polygons[0]

    actual_render_positions = [res['render_pos'] for res in results]

    expected_render_positions = [
        (-32, 0), (0, 0), (0, 0),
        (-32, 0), (0, 0), (0, 0),
        (-32, 0), (0, 0), (0, 0),
    ]

    assert expected_render_positions[0] == actual_render_positions[0]
