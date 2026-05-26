"""Allow invocation as `python -m boltzyml`.

Equivalent to the `boltzyml` console-script entry point — useful when
the install's Scripts directory is not on PATH (common on Windows).
"""

from .cli import _entry

if __name__ == "__main__":
    _entry()
