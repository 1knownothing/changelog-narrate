#!python
"""Allow `python -m narrate` to invoke the CLI."""
import sys
from narrate.cli import main

if __name__ == "__main__":
    sys.exit(main())
