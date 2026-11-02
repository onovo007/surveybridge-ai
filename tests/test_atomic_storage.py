import json

import pytest

from surveybridge.utils import cache


@pytest.mark.parametrize("persistent", [False, True])
def test_atomic_json_windows_lock_recovery_and_failure(tmp_path, monkeypatch, persistent):
    target = tmp_path / "checkpoint.json"
    target.write_text('{"old":true}', encoding="utf-8")
    replace = cache.os.replace
    attempts, waits = [], []

    def locked(source, destination):
        attempts.append(1)
        if persistent or len(attempts) < 3:
            raise PermissionError("simulated file scanner lock")
        return replace(source, destination)

    monkeypatch.setattr(cache.os, "replace", locked)
    monkeypatch.setattr(cache.time, "sleep", waits.append)
    if persistent:
        with pytest.raises(PermissionError):
            cache.atomic_json(target, {"new": True})
        assert json.loads(target.read_text()) == {"old": True}
        assert len(attempts) == 6 and len(waits) == 5
    else:
        cache.atomic_json(target, {"new": True})
        assert json.loads(target.read_text()) == {"new": True}
        assert len(attempts) == 3 and waits == [0.05, 0.1]
    assert not list(tmp_path.glob(".write-*.tmp"))
