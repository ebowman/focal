import contextlib
import io
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflow"))

import create_event
import extraction
import openai
import package_workflow


EVENT = {
    "title": "Call with Alex",
    "start_date": "2026-11-20",
    "end_date": "2026-11-20",
    "all_day": False,
    "start_time": "16:30",
    "end_time": "17:30",
    "location": None,
    "notes": None,
    "recurrence": None,
}


class ExtractionTests(unittest.TestCase):
    def test_requests_json_from_supported_model(self):
        with patch("openai.OpenAI") as factory:
            client = factory.return_value.__enter__.return_value
            client.chat.completions.create.return_value.choices[0].message.content = json.dumps(EVENT)
            result = extraction.extract_event_data("prompt", "test-key", logging.getLogger("test"))

        self.assertEqual(json.loads(result), EVENT)
        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "gpt-4.1-mini")
        self.assertEqual(request["response_format"], {"type": "json_object"})

    def test_api_failure_keeps_diagnostic(self):
        with patch("openai.OpenAI") as factory:
            client = factory.return_value.__enter__.return_value
            client.chat.completions.create.side_effect = openai.OpenAIError("model not available")
            with self.assertLogs("test", level="ERROR") as logs:
                result = extraction.extract_event_data("prompt", "test-key", logging.getLogger("test"))

        self.assertIsNone(result)
        self.assertIn("model not available", logs.output[0])

    def test_dry_run_never_executes_applescript(self):
        for app in ("calendar", "fantastical"):
            with self.subTest(app=app), contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(sys, "argv", ["create_event.py", "--dry-run", "call with Alex today at 16:30"]))
                stack.enter_context(patch.object(create_event, "get_api_key", return_value="test-key"))
                stack.enter_context(patch.object(create_event, "get_calendar_app", return_value=app))
                stack.enter_context(patch.object(create_event, "get_target_calendar", return_value="Calendar"))
                stack.enter_context(patch.object(create_event, "extract_event_data", return_value=json.dumps(EVENT)))
                execute = stack.enter_context(patch.object(create_event, "execute_applescript"))
                dispatch = stack.enter_context(patch.object(create_event, "execute_fantastical_url"))
                output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                create_event.main()
                execute.assert_not_called()
                dispatch.assert_not_called()
                self.assertIn('"start_time": "16:30"', output.getvalue())
                self.assertIn("Dry run: no event created", output.getvalue())

class FantasticalTests(unittest.TestCase):
    def test_explicit_times_calendar_and_special_characters(self):
        event = {**EVENT, "title": 'Call & "Alex" / #1', "end_time": "17:00",
                 "location": "A+B & C", "notes": "one\ntwo?add=0"}
        url = create_event.create_fantastical_url(event, "original prompt", "Work & Home", logging.getLogger("test"))
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        self.assertEqual((parsed.scheme, parsed.netloc), ("x-fantastical", "parse"))
        self.assertEqual(params["title"], [event["title"]])
        self.assertEqual(params["start"], ["2026-11-20 16:30"])
        self.assertEqual(params["end"], ["2026-11-20 17:00"])
        self.assertEqual(params["calendarName"], ["Work & Home"])
        self.assertEqual(params["location"], ["A+B & C"])
        self.assertIn(event["notes"], params["notes"][0])
        self.assertIn('Original: "original prompt"', params["notes"][0])
        self.assertEqual(params["add"], ["1"])
        self.assertNotIn("sentence", params)

    def test_all_day_range_uses_dates_without_times(self):
        event = {**EVENT, "all_day": True, "end_date": "2026-11-22",
                 "start_time": None, "end_time": None}
        url = create_event.create_fantastical_url(event, "trip", "Calendar", logging.getLogger("test"))
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params["allDay"], ["1"])
        self.assertEqual(params["start"], ["2026-11-20"])
        self.assertEqual(params["end"], ["2026-11-22"])

    def test_unsupported_recurrence_is_not_silently_discarded(self):
        with self.assertLogs("test", level="ERROR") as logs:
            url = create_event.create_fantastical_url(
                {**EVENT, "recurrence": "weekly"}, "weekly call", "Calendar", logging.getLogger("test"))
        self.assertIsNone(url)
        self.assertIn("Recurring events are not supported", logs.output[0])

    def test_dispatch_failure_reports_error(self):
        with patch.object(create_event.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 1, "", "No application handles URL")
            with self.assertLogs("test", level="ERROR") as logs:
                self.assertFalse(create_event.execute_fantastical_url("x-fantastical://parse?add=1", logging.getLogger("test")))
        self.assertEqual(run.call_args.args[0], ["/usr/bin/open", "-g", "x-fantastical://parse?add=1"])
        self.assertIn("No application handles URL", logs.output[0])


class RuntimeTests(unittest.TestCase):
    def test_packaged_venv_restores_interpreter_without_losing_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build = root / "build"
            build.mkdir()
            subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(build / "venv")], check=True)
            site_packages = next((build / "venv/lib").glob("python*/site-packages"))
            (site_packages / "bundled_dependency.py").write_text("message = 'bundled dependency works'\n")
            (build / "create_event.py").write_text("from bundled_dependency import message\nprint(message)\n")
            shutil.copy2(Path(create_event.__file__).with_name("run.sh"), build / "run.sh")
            archive_path = root / "workflow.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for path in build.rglob("*"):
                    package_workflow.add_to_archive(archive, path, build)

            installed = root / "installed"
            subprocess.run(["/usr/bin/ditto", "-xk", str(archive_path), str(installed)], check=True)
            python = installed / "venv/bin/python3"
            self.assertFalse(python.exists())
            result = subprocess.run(
                ["bash", str(installed / "run.sh"), "event"],
                env={**os.environ, "HOME": str(root)},
                capture_output=True, text=True, check=True,
            )
            self.assertTrue(python.is_symlink())
            self.assertIn("Restoring local Python", result.stdout)
            self.assertIn("bundled dependency works", result.stdout)

    def test_runner_preserves_literal_argument_and_logs_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner = root / "run.sh"
            shutil.copy2(Path(create_event.__file__).with_name("run.sh"), runner)
            bin_dir = root / "venv/bin"
            bin_dir.mkdir(parents=True)
            python = bin_dir / "python3"
            python.write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n')
            python.chmod(0o755)
            description = 'call with "Alex"; $(exit 9) at 16:30'
            result = subprocess.run(
                ["bash", str(runner), description],
                env={**os.environ, "HOME": str(root)},
                capture_output=True, text=True, check=True,
            )
            self.assertIn(description, result.stdout)
            log = root / "Library/Logs/FOCAL/focal.log"
            self.assertIn(description, log.read_text())
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
