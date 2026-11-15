#!/usr/bin/env python3
"""Run the notrain CLI without installing: python3 notrain.py ..."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from notrain.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
