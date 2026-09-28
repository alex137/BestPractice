#!/usr/bin/env python3
"""Entry point: python3 bridge/run.py {check,invite,run,scope} --config PATH.
See bridge/SETUP.md."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatbridge.cli import main  # noqa: E402

sys.exit(main())
