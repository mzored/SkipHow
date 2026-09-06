"""Keep a direct pytest run from writing bytecode into the package under test.

The package identity in `scripts/check_hosts.py` hashes every regular file under
`plugins/skiphow/`, so a `__pycache__` directory written there by a test that
imports a shipped script changes the candidate payload and fails the identity
checks. `PYTHONDONTWRITEBYTECODE` is read at interpreter startup, so setting it
here only helps the Python processes the tests spawn; `sys.dont_write_bytecode`
is what stops this interpreter, and pytest imports conftest before any test
module. `scripts/check.py` already sets the variable for the runs it starts.
"""

from __future__ import annotations

import os
import sys


sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
