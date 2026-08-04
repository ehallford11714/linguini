from linguini.hygiene import build_carag, netrin_route


def test_carag_pack() -> None:
    pack = build_carag("effect of price on demand")
    d = pack.to_dict()
    assert d["query"]
    assert "association is not causation" in d["wisdom_guardrails"]


def test_netrin_route_spurious() -> None:
    pkt = netrin_route("Demand looks like last quarter so raise price")
    assert pkt.verdict == "DIVERGENT"
    assert pkt.temperature <= 1.25
