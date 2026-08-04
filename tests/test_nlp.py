from linguini.suite.nlp import NLPSuite


def test_claim_hygiene_flags_spurious() -> None:
    nlp = NLPSuite()
    r = nlp.claim_hygiene("Demand looks like last quarter so raise price")
    assert r["spurious_causation"] is True
    assert r["ok"] is False


def test_compose() -> None:
    nlp = NLPSuite()
    r = nlp.compose_tokenize_hygiene("Hello")
    assert r["tokens"] == ["hello"]
