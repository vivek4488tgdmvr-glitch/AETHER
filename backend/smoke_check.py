"""Offline smoke checks for key project modules; does not call Nebius or run untrusted code."""
from app.repository import _is_safe_member
from app.services import extract_json

assert _is_safe_member("src/main.py")
assert not _is_safe_member("../outside.txt")
assert not _is_safe_member("/absolute/path.py")
assert extract_json('{"findings": []}') == {"findings": []}
assert extract_json('```json\n{"ok": true}\n```') == {"ok": True}
print("Offline smoke checks passed.")
