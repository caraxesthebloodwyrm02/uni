from apparat.api import (
    ComputationalQuantizationMatrix,
    GridCell,
    SpatialRender,
)


def test_grid_cell_read():
    cell = GridCell(1, 2, 42.0, "acoustic")
    assert cell.read() == 42.0


def test_quantization_matrix_in_bounds():
    cqm = ComputationalQuantizationMatrix(2, 2)
    assert cqm.resolution == (2, 2)
    assert cqm.get_cell(0, 0) == 0.0

    cqm.set_cell(1, 0, 15.5)
    assert cqm.get_cell(1, 0) == 15.5
    assert cqm.read_row(0) == [0.0, 15.5]


def test_quantization_matrix_out_of_bounds():
    cqm = ComputationalQuantizationMatrix(2, 2)

    # set_cell out of bounds should do nothing (no crash)
    cqm.set_cell(-1, 0, 99.0)
    cqm.set_cell(5, 5, 99.0)

    # get_cell out of bounds should return 0.0
    assert cqm.get_cell(-1, 0) == 0.0
    assert cqm.get_cell(2, 2) == 0.0

    # read_row out of bounds should return []
    assert cqm.read_row(-1) == []
    assert cqm.read_row(10) == []


def test_spatial_render():
    cqm = ComputationalQuantizationMatrix(2, 2)
    cqm.set_cell(0, 1, 3.14)

    render_obj = SpatialRender(cqm)
    res = render_obj.render()

    assert res == [[0.0, 0.0], [3.14, 0.0]]
    assert render_obj.read_render() == [[0.0, 0.0], [3.14, 0.0]]
