from app.services.collector_auth import hash_agent_token


def test_hash_agent_token_is_deterministic_and_not_plaintext():
    token = "sentinela_agent_example"
    hashed = hash_agent_token(token)
    assert hashed == hash_agent_token(token)
    assert hashed != token
    assert len(hashed) == 64
