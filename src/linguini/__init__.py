"""Linguini — invents novel tools from MCP + libs + skills."""

from linguini.__version__ import __version__
from linguini.api import FulfillResult, Linguini
from linguini.forge.forge import ForgeResult, create_native_tool, wrap_chain_as_native
from linguini.forge.purpose import ForgePurpose, IOExample
from linguini.invent import InventResult, invent

__all__ = [
    "__version__",
    "Linguini",
    "FulfillResult",
    "ForgeResult",
    "InventResult",
    "ForgePurpose",
    "IOExample",
    "create_native_tool",
    "wrap_chain_as_native",
    "invent",
]
