# from typing import Optional

# from ..transform import DataTransform


# class EncodingUtils:
#     @staticmethod
#     def enc_pin(pin: str) -> str:
#         return DataTransform.rpad(DataTransform.s2h(pin), 16).upper()

#     @staticmethod
#     def dec_pin(encoded_pin: str) -> str:
#         return DataTransform.h2s(encoded_pin).upper()

#     @staticmethod
#     def enc_imsi(imsi):
#         imsi = str(imsi)
#         l = DataTransform.half_round_up(
#             len(imsi) + 1
#         )  # Required bytes - include space for odd/even indicator
#         oe = len(imsi) & 1  # Odd (1) / Even (0)
#         ei = "%02x" % l + DataTransform.swap_nibbles(
#             "%01x%s" % ((oe << 3) | 1, DataTransform.rpad(imsi, 15))
#         )
#         return ei

#     @staticmethod
#     def dec_imsi(ef: str) -> Optional[str]:
#         if len(ef) < 4:
#             return None
#         l = int(ef[0:2], 16) * 2 - 1
#         swapped = DataTransform.swap_nibbles(ef[2:]).rstrip("f")
#         if len(swapped) < 1:
#             return None
#         oe = (int(swapped[0]) >> 3) & 1
#         if not oe:
#             l -= 1
#         if l != len(swapped) - 1:
#             return None
#         return swapped[1:]

#     @staticmethod
#     def enc_iccid(iccid: str) -> str:
#         luhn = EncodingUtils.calculate_luhn(iccid)
#         iccid_with_luhn = iccid + str(luhn)
#         return DataTransform.swap_nibbles(
#             DataTransform.rpad(iccid_with_luhn, 20)
#         ).upper()

#     @staticmethod
#     def dec_iccid(ef: str) -> str:
#         return DataTransform.swap_nibbles(ef.upper()).strip("F")[:-1]

#     @staticmethod
#     def calculate_luhn(cc: str) -> int:
#         num = list(map(int, str(cc)))
#         check_digit = (
#             10 - sum(num[-2::-2] + [sum(divmod(d * 2, 10)) for d in num[::-2]]) % 10
#         )
#         return 0 if check_digit == 10 else check_digit


# __all__ = ["EncodingUtils"]
from typing import Optional
from ..transform import DataTransform


class EncodingUtils:
    """
    Utility class providing encoding and decoding helpers
    for PINs, IMSIs, ICCIDs, and Luhn checksum calculations.
    """

    @staticmethod
    def enc_pin(pin: str) -> str:
        """
        Encode a PIN string into its hexadecimal padded representation.

        Args:
            pin (str): The PIN to encode.

        Returns:
            str: Uppercase hex string (16 characters long).
        """
        return DataTransform.rpad(DataTransform.s2h(pin), 16).upper()

    @staticmethod
    def dec_pin(encoded_pin: str) -> str:
        """
        Decode a previously encoded PIN back into its string form.

        Args:
            encoded_pin (str): The encoded PIN as a hex string.

        Returns:
            str: Decoded PIN string in uppercase.
        """
        return DataTransform.h2s(encoded_pin).upper()

    @staticmethod
    def enc_imsi(imsi: str) -> str:
        """
        Encode an IMSI into EF (Elementary File) format as per GSM specifications.

        Args:
            imsi (str): The IMSI (International Mobile Subscriber Identity).

        Returns:
            str: Encoded IMSI as a hex string with length/odd-even indicator.
        """
        imsi = str(imsi)
        l = DataTransform.half_round_up(
            len(imsi) + 1
        )  # Required bytes including odd/even indicator
        oe = len(imsi) & 1  # Odd (1) / Even (0)
        ei = "%02x" % l + DataTransform.swap_nibbles(
            "%01x%s" % ((oe << 3) | 1, DataTransform.rpad(imsi, 15))
        )
        return ei

    @staticmethod
    def dec_imsi(ef: str) -> Optional[str]:
        """
        Decode an encoded IMSI from EF format.

        Args:
            ef (str): Encoded IMSI as a hex string.

        Returns:
            Optional[str]: The decoded IMSI string, or None if invalid.
        """
        if len(ef) < 4:
            return None
        l = int(ef[0:2], 16) * 2 - 1
        swapped = DataTransform.swap_nibbles(ef[2:]).rstrip("f")
        if len(swapped) < 1:
            return None
        oe = (int(swapped[0]) >> 3) & 1
        if not oe:
            l -= 1
        if l != len(swapped) - 1:
            return None
        return swapped[1:]

    @staticmethod
    def enc_iccid(iccid: str) -> str:
        """
        Encode an ICCID with a Luhn check digit, padded, and nibble-swapped.

        Args:
            iccid (str): The ICCID (Integrated Circuit Card Identifier).

        Returns:
            str: Encoded ICCID as an uppercase hex string.
        """
        luhn = EncodingUtils.calculate_luhn(iccid)
        iccid_with_luhn = iccid + str(luhn)
        return DataTransform.swap_nibbles(
            DataTransform.rpad(iccid_with_luhn, 20)
        ).upper()

    @staticmethod
    def dec_iccid(ef: str) -> str:
        """
        Decode an ICCID from EF format by reversing nibble-swapping and removing padding.

        Args:
            ef (str): Encoded ICCID as a hex string.

        Returns:
            str: Decoded ICCID string (without Luhn digit).
        """
        return DataTransform.swap_nibbles(ef.upper()).strip("F")[:-1]

    @staticmethod
    def calculate_luhn(cc: str) -> int:
        """
        Compute the Luhn check digit for a numeric string.

        Args:
            cc (str): The numeric string (e.g., ICCID) to calculate check digit for.

        Returns:
            int: The Luhn check digit (0–9).
        """
        num = list(map(int, str(cc)))
        check_digit = (
            10 - sum(num[-2::-2] + [sum(divmod(d * 2, 10)) for d in num[::-2]]) % 10
        )
        return 0 if check_digit == 10 else check_digit


__all__ = ["EncodingUtils"]
