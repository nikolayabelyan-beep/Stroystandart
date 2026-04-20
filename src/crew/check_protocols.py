#!/usr/bin/env python3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.crew.protocol_guard import validate_required_sources


def main() -> int:
    result = validate_required_sources()
    if result.ok:
        print("[OK] Protocol sources check passed")
        return 0
    for err in result.errors:
        print(f"[ERROR] {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
