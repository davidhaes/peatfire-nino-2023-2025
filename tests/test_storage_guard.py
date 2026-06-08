from __future__ import annotations

import pytest

from peatfire_nino.io.storage_guard import StorageCapExceeded, enforce_cap, folder_size_gb


def test_empty_folder_zero(tmp_path) -> None:
    assert folder_size_gb(tmp_path) == 0.0


def test_warn_does_not_raise(tmp_path) -> None:
    (tmp_path / "f.bin").write_bytes(b"x" * 1024)
    # tiny file, well under caps
    assert enforce_cap(tmp_path, warn_gb=100, stop_gb=200) >= 0.0


def test_stop_raises(tmp_path) -> None:
    (tmp_path / "f.bin").write_bytes(b"x" * 2048)
    with pytest.raises(StorageCapExceeded):
        enforce_cap(tmp_path, warn_gb=0.0, stop_gb=0.0)
