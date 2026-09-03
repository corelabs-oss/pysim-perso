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
"""Inject a seeded generator so a batch is byte-for-byte reproducible.

DataGenerationScript takes its randomness from an injected object, which makes
tests able to assert on exact values. Two scripts in one process keep separate
state, so independent configurations can also be generated concurrently.

    WARNING
    Keys from a seeded PRNG are predictable. This is for tests and fixtures
    only. Never personalize cards for a real network with a seeded generator;
    the default DataGenerator draws from the OS CSPRNG for that reason.

Run:
    python examples/06_reproducible_batch.py
"""

import random
import tempfile

from pysim_perso import DataGenerationScript, json_loader

REPO_ROOT_SETTINGS = "settings.example.json"


class SeededDataGenerator:
    """Drop-in replacement for DataGenerator backed by a seeded PRNG.

    Implements the surface DataGenerationScript actually calls: generate_ki,
    generate_otas, generate_4_digit and generate_8_digit.
    """

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def _hex16(self) -> str:
        return self._rng.randbytes(16).hex().upper()

    def generate_ki(self) -> str:
        return self._hex16()

    def generate_otas(self) -> str:
        return self._hex16()

    def generate_4_digit(self) -> str:
        return f"{self._rng.randrange(10_000):04d}"

    def generate_8_digit(self) -> str:
        return f"{self._rng.randrange(100_000_000):08d}"


def generate_kis(seed: int) -> list:
    from pathlib import Path

    config = json_loader(
        str(Path(__file__).resolve().parent.parent / REPO_ROOT_SETTINGS)
    )
    config.PATHS.OUTPUT_FILES_DIR = tempfile.mkdtemp(prefix="gsm-seeded-")
    config.DISP.size = 3

    script = DataGenerationScript(config, data_generator=SeededDataGenerator(seed))
    script.json_to_global_params()
    result_dfs, _ = script.generate_all_data()
    return list(result_dfs["ELECT"]["KI"])


def main() -> None:
    first = generate_kis(seed=1234)
    second = generate_kis(seed=1234)
    different = generate_kis(seed=9999)

    print("seed 1234, run 1:")
    for ki in first:
        print(f"  {ki}")
    print()
    print(f"same seed reproduces the batch : {first == second}")
    print(f"different seed differs         : {first != different}")


if __name__ == "__main__":
    main()
