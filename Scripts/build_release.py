#!/usr/bin/env python3
"""Build a deterministic GitHub-ready release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def include(path: Path, root: Path, output: Path) -> bool:
    relative = path.relative_to(root)
    if not path.is_file() or path.resolve() == output.resolve():
        return False
    if ".git" in relative.parts or "__pycache__" in relative.parts or "tmp" in relative.parts:
        return False
    if path.suffix in {".pyc", ".zip"}:
        return False
    return True


def build(root: Path, output: Path) -> None:
    config = json.loads((root / "configs" / "evaluation.json").read_text(encoding="utf-8"))
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", config["source_date_epoch"]))
    stamp = datetime.fromtimestamp(epoch, tz=timezone.utc)
    date_time = (stamp.year, stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(candidate for candidate in root.rglob("*") if include(candidate, root, output)):
            relative = Path(root.name) / path.relative_to(root)
            info = zipfile.ZipInfo(relative.as_posix(), date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"archive: {output}")
    print(f"sha256: {digest}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
