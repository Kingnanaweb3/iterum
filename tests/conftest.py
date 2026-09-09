"""Point every test at a throwaway database.

memory.py caches one client per process and reads its path at import time,
so both are overridden here. Without this, tests would write into the same
store the demo runs on.
"""
import pytest

from iterum import memory


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(memory, "_client", None)
    yield
    memory._client = None
