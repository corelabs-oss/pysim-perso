# tests/test_data_generator.py
import re
import pytest

import gsm_data_generator.generator as generator


# -------------------------
# Tests for DataGenerator
# -------------------------
def test_generate_ki():
    ki = generator.DataGenerator.generate_ki()
    assert isinstance(ki, str)
    assert len(ki) == 32  # 16 bytes -> 32 hex chars
    assert re.fullmatch(r"[0-9A-F]+", ki)


def test_generate_otas():
    otas = generator.DataGenerator.generate_otas()
    assert isinstance(otas, str)
    assert len(otas) == 32
    assert re.fullmatch(r"[0-9A-F]+", otas)


@pytest.mark.parametrize(
    "lenght, expected",
    [
        (32, 64),
        (64, 128),
    ],
)
def test_generate_k4(lenght, expected):
    k4 = generator.DataGenerator.generate_k4(lenght)
    assert isinstance(k4, str)
    assert len(k4) == expected  # 32 bytes -> 64 hex chars
    assert re.fullmatch(r"[0-9A-F]+", k4)


def test_generate_8_digit():
    num = generator.DataGenerator.generate_8_digit()
    assert num.isdigit()
    assert len(num) == 8


def test_generate_4_digit():
    num = generator.DataGenerator.generate_4_digit()
    assert num.isdigit()
    assert len(num) == 4
