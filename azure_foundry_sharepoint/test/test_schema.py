import os
import importlib
import unittest
from contextlib import contextmanager


@contextmanager
def temp_env(key: str, value: str | None):
    """Temporarily set or unset an environment variable."""
    original = os.environ.get(key)
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value
    try:
        yield
    finally:
        if original is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original


class FakeDeltaEvent:
    def __init__(self, delta: str):
        self.type = "response.output_text.delta"
        self.delta = delta


class FakeCompletedEvent:
    def __init__(self):
        self.type = "response.completed"


class FakeResponseStream:
    def __iter__(self):
        yield FakeDeltaEvent("Hello")
        yield FakeDeltaEvent(", world")
        yield FakeCompletedEvent()


class FakeResponsesClient:
    def create(self, *, stream: bool, input: str, extra_body: dict):  # noqa: ARG002
        return FakeResponseStream()


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponsesClient()


class SharePointAppTests(unittest.TestCase):
    def test_agent_name_defaults_and_override(self):
        with temp_env("SHAREPOINT_AGENT_NAME", None):
            import main as app

            importlib.reload(app)
            self.assertEqual(app.AGENT_NAME, "sharepoint-cli-agent")

        with temp_env("SHAREPOINT_AGENT_NAME", "custom-agent"):
            import main as app

            importlib.reload(app)
            self.assertEqual(app.AGENT_NAME, "custom-agent")

    def test_stream_agent_reply_concatenates_stream(self):
        import main as app

        importlib.reload(app)

        openai_client = FakeOpenAIClient()
        result = app.stream_agent_reply(openai_client, "agent", "hi", placeholder=DummyPlaceholder())
        self.assertEqual(result, "Hello, world")


class DummyPlaceholder:
    def __init__(self):
        self._written = []

    def write(self, text):  # noqa: ANN001
        self._written.append(text)



if __name__ == "__main__":
    unittest.main()
