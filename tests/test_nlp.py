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


def test_expanded_ops() -> None:
    nlp = NLPSuite()
    text = "Acme Corp grew 12%. Hello World"
    assert len(nlp.sentences(text)) >= 1
    assert nlp.entities(text)
    assert nlp.lemmas("companies") == ["company"] or "compan" in nlp.lemmas("companies")[0]
    assert len(nlp.topic_hash(text)) == 16
    r = nlp.compose_entity_hygiene(text)
    assert r["novel"] is True
    assert "entities" in r
    assert "hygiene" in r
    assert set(nlp.op_names()) >= {
        "nlp.entities",
        "nlp.compose_entity_hygiene",
        "nlp.analyze",
    }
