# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Derive OPc, EKI and ACC without running the batch pipeline.

The derivations are plain functions on hex strings, so they can be used to
check a single card, re-derive OPc for an existing Ki, or verify a vendor's
output against this implementation.

Run:
    python examples/03_key_derivation.py
"""

from gsm_data_generator import CryptoUtils, DataGenerator, DependentDataGenerator


def main() -> None:
    # 1. Verify against the 3GPP TS 35.206 test vector. This is the same check
    #    verify.py runs in CI; if it fails, nothing else here can be trusted.
    ki = "465B5CE8B199B49FAA5F0A2EE238A6BC"
    op = "CDC202D5123E20F62B6D676AC72CB318"
    expected_opc = "CD63CB71954A9F4E48A5994E37A02BAF"

    opc = DependentDataGenerator.calculate_opc(op, ki)
    print("TS 35.206 vector")
    print(f"  Ki       {ki}")
    print(f"  OP       {op}")
    print(f"  OPc      {opc}")
    print(f"  match    {opc == expected_opc}")
    print()

    # 2. EKI is Ki encrypted under the transport key K4, which is what leaves
    #    the building. Ki itself never travels in the server file.
    k4 = "0000555500006666000077770000111100005555000066660000777700001111"
    eki = DependentDataGenerator.calculate_eki(k4, ki)
    print(f"EKI (Ki under K4)  {eki}")

    # 3. ACC is the access control class bitmask, derived from the last IMSI
    #    digit per 3GPP TS 22.011.
    for imsi in ("410010000000001", "410010000000007", "410010000000000"):
        acc = DependentDataGenerator.calculate_acc(imsi)
        print(f"ACC for IMSI ...{imsi[-1]}   {acc}")
    print()

    # 4. The primitives underneath, if you need them directly.
    ciphertext = CryptoUtils.aes_128_cbc_encrypt(op, ki)
    xored = CryptoUtils.xor_str(bytes([0x0F]) * 4, bytes([0xF0]) * 4)
    print(f"AES-128-CBC(OP, Ki) {ciphertext}")
    print(f"XOR of 0F.. and F0.. {xored.hex().upper()}")
    print()

    # 5. Fresh secrets come from the OS CSPRNG, never a seeded PRNG.
    print(f"random Ki           {DataGenerator.generate_ki()}")
    print(f"random OTA key      {DataGenerator.generate_otas()}")
    print(f"random K4 (32 hex)  {DataGenerator.generate_k4(32)}")


if __name__ == "__main__":
    main()
