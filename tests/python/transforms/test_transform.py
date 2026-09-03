import pytest
from pysim_perso.transform import DataTransform


# ------------------------
# swap_nibbles
# ------------------------
def test_swap_nibbles_even_length():
    assert DataTransform.swap_nibbles("1234") == "2143"


def test_swap_nibbles_long_string():
    assert DataTransform.swap_nibbles("A1B2C3D4") == "1A2B3C4D"


# ------------------------
# rpad & lpad
# ------------------------
def test_rpad():
    assert DataTransform.rpad("abc", 6) == "abcfff"
    assert DataTransform.rpad("abc", 3) == "abc"  # no padding


def test_lpad():
    assert DataTransform.lpad("abc", 6) == "fffabc"
    assert DataTransform.lpad("abc", 3) == "abc"  # no padding


# ------------------------
# half_round_up
# ------------------------
@pytest.mark.parametrize("n, expected", [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3)])
def test_half_round_up(n, expected):
    assert DataTransform.half_round_up(n) == expected


# ------------------------
# h2b & b2h
# ------------------------
def test_h2b_and_b2h():
    hex_str = "48656c6c6f"  # "Hello"
    bytes_out = DataTransform.h2b(hex_str)
    assert isinstance(bytes_out, bytearray)
    assert DataTransform.b2h(bytes_out) == hex_str


# ------------------------
# h2i & i2h
# ------------------------
def test_h2i_and_i2h_roundtrip():
    hex_str = "4a4b4c"
    ints = DataTransform.h2i(hex_str)
    assert isinstance(ints, list)
    assert all(isinstance(x, int) for x in ints)
    assert DataTransform.i2h(ints) == hex_str


# ------------------------
# h2s & s2h
# ------------------------
def test_s2h_and_h2s_roundtrip():
    s = "Test!"
    hex_str = DataTransform.s2h(s)
    recovered = DataTransform.h2s(hex_str)
    assert recovered == s


def test_h2s_filters_ff():
    # "ff" should be ignored
    hex_str = "4142ff4344"  # AB CD, with ff ignored
    assert DataTransform.h2s(hex_str) == "ABCD"


# ------------------------
# i2s
# ------------------------
def test_i2s():
    ints = [65, 66, 67]
    assert DataTransform.i2s(ints) == "ABC"
