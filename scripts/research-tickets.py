#!/usr/bin/env python3
"""Local research tickets; no external service or automatic enrollment."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'meta/research-tickets/scripts'))
from issues import main

if __name__ == '__main__':
    raise SystemExit(main())
