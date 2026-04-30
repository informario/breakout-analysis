from app.batch_optimize import parse_row_selector


def test_parse_row_selector_all():
	assert list(parse_row_selector(":", 5)) == [0, 1, 2, 3, 4]


def test_parse_row_selector_slice():
	assert list(parse_row_selector("1:4", 6)) == [1, 2, 3]
	assert list(parse_row_selector("0:6:2", 6)) == [0, 2, 4]


def test_parse_row_selector_list():
	assert list(parse_row_selector("0,2,4", 5)) == [0, 2, 4]


def test_parse_row_selector_single():
	assert list(parse_row_selector("3", 5)) == [3]

