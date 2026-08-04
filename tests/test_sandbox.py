from linguini.sandbox.policy import SandboxPolicy
from linguini.sandbox.runner import static_scan


def test_blocks_socket_import() -> None:
    src = "import socket\ndef run():\n    return socket.gethostname()\n"
    v = static_scan(src, SandboxPolicy())
    assert any("socket" in x for x in v)


def test_allows_linguini_suite() -> None:
    src = "from linguini.suite.nlp import NLPSuite\ndef run(text=''):\n    return NLPSuite().tokenize(text)\n"
    assert static_scan(src, SandboxPolicy()) == []
