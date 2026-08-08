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
"""Encode and decode the GSM elementary files, and check an ICCID.

EncodingUtils converts between human-readable values and the on-card byte
layout defined in 3GPP TS 31.102. Every encoder here has a matching decoder,
so a round trip is the quickest way to confirm a value is well-formed.

Run:
    python examples/04_encoding.py
"""

from gsm_data_generator import EncodingUtils


def main() -> None:
    # EF_IMSI: length prefix, parity nibble, then swapped BCD digits.
    imsi = "410010000000001"
    ef_imsi = EncodingUtils.enc_imsi(imsi)
    print("EF_IMSI")
    print(f"  plain    {imsi}")
    print(f"  encoded  {ef_imsi}")
    print(f"  decoded  {EncodingUtils.dec_imsi(ef_imsi)}")
    print(f"  round trip ok: {EncodingUtils.dec_imsi(ef_imsi) == imsi}")
    print()

    # EF_ICCID: swapped BCD, no length prefix.
    iccid = "8944000000000000001"
    ef_iccid = EncodingUtils.enc_iccid(iccid)
    print("EF_ICCID")
    print(f"  plain    {iccid}")
    print(f"  encoded  {ef_iccid}")
    print(f"  decoded  {EncodingUtils.dec_iccid(ef_iccid)}")
    print()

    # PINs are ASCII, right-padded with 0xFF to eight bytes.
    pin = "1234"
    ef_pin = EncodingUtils.enc_pin(pin)
    print("PIN")
    print(f"  plain    {pin}")
    print(f"  encoded  {ef_pin}")
    print(f"  decoded  {EncodingUtils.dec_pin(ef_pin)}")
    print()

    # ITU-T E.118 check digit. An ICCID whose final digit is wrong will be
    # rejected by personalization equipment, so validate before generating.
    print("E.118 check digit (Luhn)")
    body = "894400000000000000"  # 18 digits, check digit not yet appended
    check_digit = EncodingUtils.calculate_luhn(body)
    print(f"  body        {body}")
    print(f"  check digit {check_digit}")
    print(f"  full ICCID  {body}{check_digit}")

    # Validating an ICCID you were given: recompute the digit and compare.
    for candidate in ("8944000000000000001", "8944000000000000009"):
        valid = EncodingUtils.calculate_luhn(candidate[:-1]) == int(candidate[-1])
        print(f"  {candidate} valid: {valid}")


if __name__ == "__main__":
    main()
