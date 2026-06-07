# tests/test_encoding_utils.py
import pytest
from gsm_data_generator.algorithm import EncodingUtils


# -------------------------
# Tests for enc/dec PIN
# -------------------------
def test_enc_dec_pin_roundtrip():
    # Mock DataTransform functions for predictable behavior

    pin = "1234"
    encoded = EncodingUtils.enc_pin(pin)
    decoded = EncodingUtils.dec_pin(encoded)
    assert decoded.startswith("1234")


# -------------------------
# Tests for IMSI encoding/decoding
# -------------------------
def test_enc_dec_imsi_roundtrip():
    imsi = "123456789012345"
    encoded = EncodingUtils.enc_imsi(
        imsi,
    )
    decoded = EncodingUtils.dec_imsi(encoded)
    assert decoded == imsi


def test_dec_imsi_too_short():
    assert EncodingUtils.dec_imsi("12") is None


def test_dec_imsi_invalid_length():
    # malformed EF should return None
    bad = "021234"  # inconsistent length encoding
    assert EncodingUtils.dec_imsi(bad) is None


# -------------------------
# Tests for ICCID encoding/decoding
# -------------------------
def test_enc_dec_iccid_roundtrip():
    iccid = "8986001234567890123"
    encoded = EncodingUtils.enc_iccid(iccid)
    decoded = EncodingUtils.dec_iccid(encoded)
    assert decoded == iccid


def test_dec_iccid_strips_filler():
    iccid = "898600987654321"
    encoded = EncodingUtils.enc_iccid(iccid)
    # add filler manually
    encoded_with_filler = encoded + "F" * 10
    decoded = EncodingUtils.dec_iccid(encoded_with_filler)
    assert decoded == iccid


# -------------------------
# Tests for Luhn calculation
# -------------------------
@pytest.mark.parametrize(
    "cc,expected",
    [
        ("7992739871", 3),  # standard Luhn example
        ("123456789", 7),
        ("400000000000000", 2),
    ],
)
def test_calculate_luhn(cc, expected):
    assert EncodingUtils.calculate_luhn(cc) == expected
