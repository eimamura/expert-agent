from __future__ import annotations

import ulid


def new_run_id() -> str:
    return str(ulid.new())
