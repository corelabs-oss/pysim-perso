from Crypto.Cipher import AES
import binascii


class CryptoUtils:
    """
    Low-level cryptographic utilities for AES encryption
    and XOR operations used in GSM/3GPP authentication algorithms.
    """

    @staticmethod
    def aes_128_cbc_encrypt(key: str, text: str) -> str:
        """
        Perform AES-128 CBC encryption with a zero IV.

        Args:
            key (str): 32-character hex string (16 bytes) representing the AES key (e.g., K or transport key).
            text (str): Hex string (multiples of 16 bytes) representing the plaintext.

        Returns:
            str: Ciphertext as an uppercase hex string.
        """
        iv = binascii.unhexlify("00" * 16)
        key_bytes = binascii.unhexlify(key)
        text_bytes = binascii.unhexlify(text)
        encryptor = AES.new(key_bytes, AES.MODE_CBC, IV=iv)
        ciphertext = encryptor.encrypt(text_bytes)
        return ciphertext.hex().upper()

    @staticmethod
    def xor_str(s: bytes, t: bytes) -> bytes:
        """
        Perform XOR between two byte strings of equal length.

        Args:
            s (bytes): First byte string.
            t (bytes): Second byte string.

        Returns:
            bytes: Result of byte-wise XOR.
        """
        return bytes([_a ^ _b for _a, _b in zip(s, t)])

    @staticmethod
    def calc_opc_hex(k_hex: str, op_hex: str) -> str:
        """
        Calculate the OPc value used in 3GPP AKA (Authentication and Key Agreement).

        OPc is derived as: OPc = AES_K(OP) ⊕ OP

        Args:
            k_hex (str): Subscriber key K as a 32-character hex string.
            op_hex (str): Operator variant configuration field OP as a 32-character hex string.

        Returns:
            str: The calculated OPc value as an uppercase hex string.
        """
        iv = binascii.unhexlify("00" * 16)
        ki = binascii.unhexlify(k_hex)
        op = binascii.unhexlify(op_hex)
        aes_crypt = AES.new(ki, mode=AES.MODE_CBC, IV=iv)
        o_pc = CryptoUtils.xor_str(op, aes_crypt.encrypt(op))
        return o_pc.hex().upper()


class DependentDataGenerator:
    """
    Higher-level data generators that depend on cryptographic primitives,
    such as OPc, Eki, and ACC values used in SIM/USIM contexts.
    """

    @staticmethod
    def calculate_opc(op: str, ki: str) -> str:
        """
        Generate the OPc value from OP and Ki.

        Args:
            op (str): Operator variant configuration field OP (hex string).
            ki (str): Subscriber key Ki (hex string).

        Returns:
            str: Calculated OPc as uppercase hex string.
        """
        return CryptoUtils.calc_opc_hex(ki, op).upper()

    @staticmethod
    def calculate_eki(transport: str, ki: str) -> str:
        """
        Generate the encrypted Ki (Eki) using AES-128 CBC with a zero IV.

        Args:
            transport (str): Transport key as a 32-character hex string.
            ki (str): Subscriber key Ki as a 32-character hex string.

        Returns:
            str: Encrypted Ki (Eki) as uppercase hex string.
        """
        return CryptoUtils.aes_128_cbc_encrypt(transport, ki)

    @staticmethod
    def calculate_acc(imsi: str) -> str:
        """
        Calculate the Access Control Class (ACC) value from an IMSI.

        ACC is defined as a bitmask where the bit at position `last_digit(IMSI)` is set.

        Args:
            imsi (str): IMSI (International Mobile Subscriber Identity) as a string.

        Returns:
            str: ACC as a 4-digit lowercase hex string.
        """
        last_digit = int(imsi[-1])
        acc_binary = bin(1 << last_digit)[2:].zfill(16)
        return format(int(acc_binary, 2), "04x")


__all__ = ["DependentDataGenerator", "CryptoUtils"]
