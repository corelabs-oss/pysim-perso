from Crypto.Cipher import AES
from Crypto.Util.strxor import strxor
import binascii

# AES block size in bytes. Ki and OP are each exactly one block, which is what
# makes the single-block CBC/ECB equivalence below hold.
BLOCK_SIZE = 16


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
        if len(s) != len(t):
            # zip() used to truncate to the shorter input; strxor rejects a
            # length mismatch, so truncate explicitly to keep that behaviour.
            shortest = min(len(s), len(t))
            s, t = s[:shortest], t[:shortest]
        return strxor(bytes(s), bytes(t))

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
        ki = binascii.unhexlify(k_hex)
        op = binascii.unhexlify(op_hex)
        # OP is exactly one block, so CBC with a zero IV is identical to ECB.
        # ECB avoids rebuilding the IV on every card. Verified against the
        # TS 35.206 test vector in verify.py.
        aes_crypt = AES.new(ki, mode=AES.MODE_ECB)
        o_pc = CryptoUtils.xor_str(op, aes_crypt.encrypt(op))
        return o_pc.hex().upper()


class TransportKeyCipher:
    """Encrypts Ki under a transport key that is fixed for a whole batch.

    ``calculate_eki`` builds a fresh AES object per card, and constructing the
    cipher costs more than the encryption itself — it was 27% of a generation
    run. The transport key is constant across a batch and Ki is exactly one
    block, so the cipher can be built once and reused: CBC with a zero IV over
    a single block is identical to ECB, and ECB holds no chaining state.

    The single-block property is what makes this safe, so it is enforced
    rather than assumed. Instances hold a key schedule; give one the same
    lifetime as the batch it belongs to.
    """

    def __init__(self, transport_hex: str):
        self.key_hex = transport_hex
        self._cipher = AES.new(binascii.unhexlify(transport_hex), AES.MODE_ECB)

    def encrypt_ki(self, ki_hex: str) -> str:
        """Return EKI for one Ki, as an uppercase hex string."""
        block = binascii.unhexlify(ki_hex)
        if len(block) != BLOCK_SIZE:
            raise ValueError(
                f"Ki must be exactly {BLOCK_SIZE} bytes to reuse the transport "
                f"cipher, got {len(block)}"
            )
        return self._cipher.encrypt(block).hex().upper()


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


__all__ = ["DependentDataGenerator", "CryptoUtils", "TransportKeyCipher"]
