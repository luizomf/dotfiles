import json
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / "scripts" / "pi_parse_json"


class PiParseJsonTests(unittest.TestCase):
    def run_parser(self, events, *, force_color=False):
        input_text = "".join(json.dumps(event) + "\n" for event in events)
        env = os.environ.copy()
        env["NO_COLOR" if not force_color else "FORCE_COLOR"] = "1"
        env.pop("FORCE_COLOR" if not force_color else "NO_COLOR", None)
        result = subprocess.run(
            [PARSER],
            input=input_text,
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        return result.stdout

    def test_parses_live_json_events(self):
        events = [
            {
                "type": "message_update",
                "assistantMessageEvent": {"type": "thinking_delta", "delta": "Thinking"},
            },
            {
                "type": "message_update",
                "assistantMessageEvent": {"type": "text_delta", "delta": "OK"},
            },
            {
                "type": "tool_execution_start",
                "toolName": "read",
                "args": {"path": "example.txt"},
            },
            {"type": "tool_execution_end", "toolName": "read", "isError": False},
            {"type": "agent_end"},
        ]

        self.assertEqual(
            self.run_parser(events),
            'ThinkingOK\n→ read: {"path":"example.txt"}\n\n← read: ok\n\n',
        )

    def test_force_color_when_output_is_not_a_tty(self):
        events = [
            {
                "type": "message_update",
                "assistantMessageEvent": {"type": "thinking_delta", "delta": "Thinking"},
            },
        ]

        self.assertEqual(
            self.run_parser(events, force_color=True),
            "\x1b[90mThinking\x1b[0m",
        )

    def test_parses_persisted_session_events(self):
        events = [
            {"type": "session", "id": "example"},
            {
                "type": "message",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "thinking", "thinking": "Thinking"},
                        {
                            "type": "toolCall",
                            "id": "call-1",
                            "name": "read",
                            "arguments": {"path": "example.txt"},
                        },
                    ],
                },
            },
            {
                "type": "message",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call-1",
                    "toolName": "read",
                    "isError": False,
                    "content": [{"type": "text", "text": "file contents"}],
                },
            },
            {
                "type": "message",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Done."}],
                },
            },
        ]

        self.assertEqual(
            self.run_parser(events),
            'Thinking\n→ read: {"path":"example.txt"}\n\n← read: ok\nDone.',
        )


if __name__ == "__main__":
    unittest.main()
