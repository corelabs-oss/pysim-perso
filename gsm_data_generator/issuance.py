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
"""Persistent record of which identifier ranges have already been issued."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .error import IssuanceOverlapError

LEDGER_FILENAME = ".issuance_ledger.json"


class IssuanceLedger:
    """Tracks issued ICCID and IMSI ranges so a batch is never issued twice.

    Running the same configuration twice produces identical ICCID and IMSI
    sequences but fresh, unrelated Ki values. Two physical cards would then
    carry the same ICCID with different keys, and neither could be provisioned
    reliably — the HLR keys the subscriber by ICCID/IMSI. Nothing else in the
    library detects this, so the ledger makes it an error.

    The ledger lives beside the generated output, in
    ``PATHS.OUTPUT_FILES_DIR``, and needs no configuration of its own.
    """

    def __init__(self, directory, filename: str = LEDGER_FILENAME):
        self.directory = Path(directory)
        self.path = self.directory / filename

    # ------------------------------------------------------------------ #
    # Reading
    # ------------------------------------------------------------------ #

    def records(self) -> List[dict]:
        """Return every recorded batch, oldest first."""
        if not self.path.exists():
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise IssuanceOverlapError(
                f"Issuance ledger at {self.path} is corrupt and cannot be "
                f"read ({exc}). Refusing to issue without a usable history — "
                f"repair or remove the file deliberately."
            ) from exc
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------ #
    # Checking
    # ------------------------------------------------------------------ #

    @staticmethod
    def _overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
        # Compared numerically so that differing zero-padding does not matter.
        return int(start_a) <= int(end_b) and int(start_b) <= int(end_a)

    def check(
        self,
        iccid_start: str,
        iccid_end: str,
        imsi_start: str,
        imsi_end: str,
    ) -> None:
        """Raise if this batch would re-issue any previously issued identifier.

        Raises
        ------
        IssuanceOverlapError
            Naming the conflicting batch and which identifier collided.
        """
        for record in self.records():
            for kind, start, end in (
                ("ICCID", iccid_start, iccid_end),
                ("IMSI", imsi_start, imsi_end),
            ):
                previous_start = record.get(f"{kind.lower()}_start")
                previous_end = record.get(f"{kind.lower()}_end")
                if previous_start is None or previous_end is None:
                    continue
                if self._overlaps(start, end, previous_start, previous_end):
                    raise IssuanceOverlapError(
                        f"{kind} range {start}-{end} overlaps batch "
                        f"{record.get('batch', '?')} "
                        f"({previous_start}-{previous_end}, issued "
                        f"{record.get('issued_at', 'at an unknown time')}). "
                        f"Re-issuing would produce duplicate {kind}s with "
                        f"different Ki values. Advance the starting "
                        f"{kind} or remove {self.path} deliberately."
                    )

    # ------------------------------------------------------------------ #
    # Recording
    # ------------------------------------------------------------------ #

    def record(
        self,
        iccid_start: str,
        iccid_end: str,
        imsi_start: str,
        imsi_end: str,
        size: int,
        issued_at: Optional[str] = None,
    ) -> dict:
        """Append a batch to the ledger and return the stored record."""
        existing = self.records()
        entry = {
            "batch": len(existing) + 1,
            "iccid_start": iccid_start,
            "iccid_end": iccid_end,
            "imsi_start": imsi_start,
            "imsi_end": imsi_end,
            "size": size,
            "issued_at": issued_at
            or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        existing.append(entry)
        self._write(existing)
        return entry

    def _write(self, records: List[dict]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        # Write to a sibling temp file and replace, so an interrupted write
        # cannot leave a truncated ledger behind.
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
            handle.write("\n")
        os.replace(temp_path, self.path)


__all__ = ["IssuanceLedger", "LEDGER_FILENAME"]
