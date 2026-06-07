import secrets
from typing import Literal


class DataGenerator:
    @staticmethod
    def generate_ki() -> str:
        """
        Generate a random 16-byte Ki value.

        The Ki (Key Identifier) is typically used in GSM authentication.
        This function generates 16 random bytes and returns them as a
        32-character uppercase hexadecimal string.

        Returns:
            str: A 32-character hexadecimal string representing the Ki.
        """
        return secrets.token_hex(16).upper()

    @staticmethod
    def generate_otas() -> str:
        """
        Generate a random 16-byte OTA key.

        OTA (Over-the-Air) keys are commonly used in SIM/USIM provisioning.
        This function generates 16 random bytes and returns them as a
        32-character uppercase hexadecimal string.

        Returns:
            str: A 32-character hexadecimal string representing the OTA key.
        """
        return secrets.token_hex(16).upper()

    @staticmethod
    def generate_k4(length: Literal[32, 64]) -> str:
        """
        Generate a random transport key (K4).

        The function generates either a 32-byte or 64-byte random key,
        returning it as an uppercase hexadecimal string.

        Args:
            length (Literal[32, 64]): The number of random bytes to generate.
                - 32 → returns a 64-character hex string.
                - 64 → returns a 128-character hex string.

        Returns:
            str: An uppercase hexadecimal string of length `length * 2`.

        Raises:
            ValueError: If the provided length is not 32 or 64.
        """
        if length not in (32, 64):
            raise ValueError("length must be either 32 or 64")
        return secrets.token_hex(length).upper()

    @staticmethod
    def generate_8_digit() -> str:
        """
        Generate a secure random 8-digit number.

        Returns:
            str: A string containing an 8-digit number (range: 10000000–99999999).
        """
        return str(secrets.SystemRandom().randint(10000000, 99999999))

    @staticmethod
    def generate_4_digit() -> str:
        """
        Generate a secure random 4-digit number.

        Returns:
            str: A string containing a 4-digit number (range: 1000–9999).
        """
        return str(secrets.SystemRandom().randint(1000, 9999))


__all__ = ["DataGenerator"]
