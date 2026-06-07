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
"""
verify.py — End-to-end smoke test for gsm-data-generator.

Usage
-----
    python verify.py                    # uses settings.json in current dir
    python verify.py --config path.json # uses a custom config file
    python verify.py --no-pipeline      # skip the full pipeline check

Exit codes: 0 = all checks passed, 1 = one or more checks failed.
"""
import sys
import argparse
from pathlib import Path

PASS = "  PASS"
FAIL = "  FAIL"
SKIP = "  SKIP"


def section(title: str) -> None:
    print(f"\n[{title}]")


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = PASS if ok else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"{status}  {label}{suffix}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify gsm-data-generator works end-to-end.")
    parser.add_argument("--config", default="settings.json", help="Path to settings JSON (default: settings.json)")
    parser.add_argument("--no-pipeline", action="store_true", help="Skip the full pipeline check")
    args = parser.parse_args()

    print("=" * 60)
    print("  GSM Data Generator — Verification")
    print("=" * 60)

    failures = 0

    # ------------------------------------------------------------------ #
    # 1. Import check
    # ------------------------------------------------------------------ #
    section("1/4  Imports")
    try:
        import gsm_data_generator
        from gsm_data_generator import (
            DataGenerator,
            DependentDataGenerator,
            CryptoUtils,
            EncodingUtils,
            DataGenerationScript,
            json_loader,
        )
        ok = check("gsm_data_generator", True, f"version {gsm_data_generator.__version__}")
    except ImportError as exc:
        ok = check("gsm_data_generator", False, str(exc))
        failures += 1
        print("\nInstall the library first:  pip install -e .")
        return 1

    # ------------------------------------------------------------------ #
    # 2. Random generator checks
    # ------------------------------------------------------------------ #
    section("2/4  Random generators")

    ki = DataGenerator.generate_ki()
    failures += 0 if check("Ki  (32 hex chars, uppercase)", len(ki) == 32 and ki == ki.upper(), ki) else 1

    ota = DataGenerator.generate_otas()
    failures += 0 if check("OTA (32 hex chars, uppercase)", len(ota) == 32 and ota == ota.upper(), ota) else 1

    k4_32 = DataGenerator.generate_k4(32)
    failures += 0 if check("K4  (64 hex chars, length=32)", len(k4_32) == 64, k4_32[:16] + "...") else 1

    k4_64 = DataGenerator.generate_k4(64)
    failures += 0 if check("K4  (128 hex chars, length=64)", len(k4_64) == 128, k4_64[:16] + "...") else 1

    pin = DataGenerator.generate_4_digit()
    failures += 0 if check("PIN (4 digits)", len(pin) == 4 and pin.isdigit(), pin) else 1

    puk = DataGenerator.generate_8_digit()
    failures += 0 if check("PUK (8 digits)", len(puk) == 8 and puk.isdigit(), puk) else 1

    # ------------------------------------------------------------------ #
    # 3. Cryptographic operations
    # ------------------------------------------------------------------ #
    section("3/4  Cryptographic operations")

    op        = "00001111000022220000333300004444"
    transport = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    imsi      = "410092078615999"

    opc = DependentDataGenerator.calculate_opc(op, ki)
    failures += 0 if check("OPC (OPc = AES_Ki(OP) XOR OP)", len(opc) == 32, opc) else 1

    eki = DependentDataGenerator.calculate_eki(transport, ki)
    failures += 0 if check("EKI (AES-128 CBC encrypted Ki)", len(eki) == 32, eki) else 1

    acc = DependentDataGenerator.calculate_acc(imsi)
    failures += 0 if check("ACC (bitmask from last IMSI digit)", len(acc) == 4, acc) else 1

    # Deterministic test vector (3GPP TS 35.206 example)
    known_ki  = "465B5CE8B199B49FAA5F0A2EE238A6BC"
    known_op  = "CDC202D5123E20F62B6D676AC72CB318"
    known_opc = "CD63CB71954A9F4E48A5994E37A02BAF"
    computed  = DependentDataGenerator.calculate_opc(known_op, known_ki)
    failures += 0 if check("OPC test vector (3GPP TS 35.206)", computed == known_opc, computed) else 1

    # Known XOR sanity
    result = CryptoUtils.xor_str(b"\xFF\x00", b"\xFF\xFF")
    failures += 0 if check("XOR sanity (0xFF^0xFF=0x00, 0x00^0xFF=0xFF)", result == b"\x00\xFF", str(result)) else 1

    # Encoding round-trip
    encoded_pin = EncodingUtils.enc_pin("1234")
    decoded_pin = EncodingUtils.dec_pin(encoded_pin)
    failures += 0 if check("PIN encode/decode round-trip", decoded_pin == "1234", f"{encoded_pin!r} -> {decoded_pin!r}") else 1

    # ------------------------------------------------------------------ #
    # 4. Full pipeline (settings.json)
    # ------------------------------------------------------------------ #
    section("4/4  Full pipeline")

    if args.no_pipeline:
        print(f"{SKIP}  skipped (--no-pipeline)")
    else:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"{SKIP}  {args.config} not found — skipping pipeline check")
            print("       Supply a config file with --config or run from the repo root.")
        else:
            try:
                config = json_loader(str(config_path))
                script = DataGenerationScript(config)
                script.json_to_global_params()

                from gsm_data_generator import Parameters
                p = Parameters.get_instance()
                params_ok = p.check_params()
                failures += 0 if check("Parameters validation", params_ok) else 1

                result_dfs, keys = script.generate_all_data()
                failures += 0 if check("Pipeline completed without error", True) else 1

                for name, df in result_dfs.items():
                    ok = not df.empty
                    failures += 0 if check(f"  {name} DataFrame ({len(df)} rows × {len(df.columns)} cols)", ok) else 1

                check("K4 present in keys", bool(keys.get("k4")), keys.get("k4", "")[:8] + "...")
                check("OP present in keys", bool(keys.get("op")), keys.get("op", "")[:8] + "...")

            except Exception as exc:
                check("Pipeline", False, str(exc))
                failures += 1

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 60)
    if failures == 0:
        print("  All checks passed.")
    else:
        print(f"  {failures} check(s) FAILED.")
    print("=" * 60)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
