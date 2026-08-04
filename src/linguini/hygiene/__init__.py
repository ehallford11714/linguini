"""Secondary hygiene: CARAG dual-band + Netrin-style routing (not the product hero)."""

from linguini.hygiene.carag import CARAGPack, build_carag
from linguini.hygiene.netrin import NetrinPacket, netrin_route

__all__ = ["CARAGPack", "build_carag", "NetrinPacket", "netrin_route"]
