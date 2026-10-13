import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("remote_log", ROOT / "src" / "remote_log.py")
remote_log = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(remote_log)

class ParserTests(unittest.TestCase):
    def rec(self, tool, args=None, text=""):
        return {
            "timestamp": "2026-09-26T05:00:00Z",
            "toolName": tool,
            "arguments": args or {},
            "output": {"content": [{"type": "text", "text": text}]},
            "duration": 10,
        }

    def test_start_process_waiting(self):
        r = self.rec(
            "start_process",
            {"command": "python -m unittest"},
            "Process started with PID 35776\nProcess 35776 is waiting for input",
        )
        level, title, details = remote_log.classify(r)
        self.assertEqual(level, "wait")
        self.assertIn("35776", title)
        self.assertTrue(any("python -m unittest" in item for item in details))
    def test_read_file(self):
        r = self.rec(
            "read_file",
            {"path": r"C:\Users\me\a\state.json"},
            "[Reading last 8 lines (total: 596 lines)]",
        )
        level, title, details = remote_log.classify(r)
        self.assertEqual(level, "ok")
        self.assertEqual(title, "读取文件")
        self.assertTrue(any("state.json" in x for x in details))

    def test_git_crlf_warning(self):
        r = self.rec(
            "start_process",
            {"command": "git diff --check"},
            "warning: in the working copy of 'VERSION', LF will be replaced by CRLF",
        )
        level, _, details = remote_log.classify(r)
        self.assertEqual(level, "warn")
        self.assertTrue(any("LF/CRLF" in x for x in details))

    def test_redaction(self):
        text = "Authorization: Bearer abcdef123456 token=secretvalue sk-1234567890abcdef"
        clean = remote_log.redact(text)
        self.assertNotIn("abcdef123456", clean)
        self.assertNotIn("secretvalue", clean)
        self.assertNotIn("sk-1234567890abcdef", clean)

    def test_stream_received_and_multiline_completed(self):
        state = {}
        received = (
            '?? Received tool call call-1: start_process '
            '{"command":"python -m unittest"} metadata: '
            '{"origin_instance":"instance-abc"}'
        )
        completed_header = '? Tool call start_process completed:'
        completed_json = (
            '{"content":[{"type":"text","text":"Process started with PID 1234\\n'
            'Process 1234 is waiting for input"}]}'
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertFalse(remote_log.parse_stream_line(received, state))
            self.assertFalse(remote_log.parse_stream_line(completed_header, state))
            self.assertFalse(remote_log.parse_stream_line(completed_json, state))
        text = buf.getvalue()
        self.assertIn("开始", text)
        self.assertIn("python -m unittest", text)
        self.assertIn("instance-abc", text)
        self.assertIn("1234", text)

    def test_stream_end_marker(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            done = remote_log.parse_stream_line(
                "__REMOTE_LOG_EXPLAINER_SESSION_END__ exit=0", {}
            )
        self.assertTrue(done)
        self.assertIn("exit 0", buf.getvalue())

if __name__ == "__main__":
    unittest.main()
