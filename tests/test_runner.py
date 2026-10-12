import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("remote_runner", ROOT / "src" / "remote_runner.py")
remote_runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(remote_runner)


class RunnerTests(unittest.TestCase):
    def test_latest_command_is_noninteractive(self):
        command = remote_runner.build_command("@wonderwhy-er/desktop-commander@latest")
        self.assertEqual(
            command,
            [
                "cmd.exe",
                "/d",
                "/c",
                "npx.cmd",
                "--yes",
                "@wonderwhy-er/desktop-commander@latest",
                "remote",
            ],
        )

    def test_pinned_version_is_preserved(self):
        command = remote_runner.build_command("@wonderwhy-er/desktop-commander@0.2.52")
        self.assertIn("--yes", command)
        self.assertIn("@wonderwhy-er/desktop-commander@0.2.52", command)
        self.assertEqual(command[-1], "remote")

    def test_other_packages_are_rejected(self):
        with self.assertRaises(ValueError):
            remote_runner.build_command("some-other-package@latest")


if __name__ == "__main__":
    unittest.main()
