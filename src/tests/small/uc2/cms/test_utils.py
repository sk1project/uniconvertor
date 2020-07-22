from uc2.cms import utils


def test_val_100():
    assert utils.val_100([0.1, 0.02, 0.009]) == [10, 2, 1]
    assert utils.val_100([0.0, 1.02, 0.909]) == [0, 102, 91]


def test_val_255():
    assert utils.val_255([0.1, 0.02, 0.009]) == [26, 5, 2]
    assert utils.val_255([0.0, 1.02, -0.1]) == [0, 260, -26]


def test_val_255_to_dec():
    assert utils.val_255_to_dec([255, 102, 204]) == [1.0, 0.4, 0.8]


def test_val_100_to_dec():
    assert utils.val_100_to_dec([255, 102, 56]) == [2.55, 1.02, 0.56]


def test_mix_vals():
    assert utils.mix_vals(0.1, 0.3, 0.5) == 0.2
    assert utils.mix_vals(0.3, 0.1, 0.5) == 0.2


def test_mix_lists():
    assert utils.mix_lists([0.1, 0.3], [0.3, 0.1], 0.5) == [0.2, 0.2]
    assert utils.mix_lists([0.1, 0.3, 6], [0.3, 0.1], 0.5) is None
