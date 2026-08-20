from app.core.hashing import stable_hash


def test_stable_hash_normalizes_spacing_and_case() -> None:
    assert stable_hash("  Hello   World ") == stable_hash("hello world")

