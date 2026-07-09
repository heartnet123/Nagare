from middleware.auth import hash_password, verify_password


def test_hash_password_and_verify_password_round_trip() -> None:
    hashed = hash_password("password123")

    assert hashed.startswith("$2")
    assert verify_password("password123", hashed) is True
    assert verify_password("wrong-password", hashed) is False
