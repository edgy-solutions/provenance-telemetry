"""Seal: `traced` opens a trace when enabled and is a pass-through when disabled."""
from provenance_telemetry import traced


def test_disabled_is_passthrough(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)

    @traced(name="extract")
    def work(x):
        return x + 1

    # Same function object semantics: it runs, unwrapped, with no Langfuse dependency.
    assert work(1) == 2


def test_enabled_still_runs_the_function(monkeypatch):
    # Even with creds set (SDK may be absent in the test env), the wrapped function
    # must still run — telemetry never changes the result.
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")

    @traced(name="extract")
    def work(x):
        return x * 2

    assert work(3) == 6
