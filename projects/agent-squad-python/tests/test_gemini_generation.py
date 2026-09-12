"""Unit tests for Gemini-backed daily content generation."""

import os
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import MagicMock, patch

from google.genai import errors

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_email as daily


def response(text="完整内容。", reason="STOP"):
    return SimpleNamespace(
        text=text,
        candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name=reason))],
    )


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.generate = MagicMock()
        fake_client = SimpleNamespace(
            models=SimpleNamespace(generate_content=self.generate)
        )
        self.client_patch = patch.object(daily, "client", fake_client)
        self.client_patch.start()
        self.sleep_patch = patch.object(daily.time, "sleep")
        self.sleep = self.sleep_patch.start()

    def tearDown(self):
        self.sleep_patch.stop()
        self.client_patch.stop()

    def test_request_and_text(self):
        self.generate.return_value = response()
        self.assertEqual(daily.collect("系统", "用户", max_tokens=320), "完整内容。")
        call = self.generate.call_args.kwargs
        self.assertEqual(call["model"], "gemini-2.5-flash-lite")
        self.assertEqual(call["contents"], "用户")
        config = call["config"].model_dump(exclude_none=True)
        self.assertEqual(config["system_instruction"], "系统")
        self.assertEqual(config["max_output_tokens"], 320)
        self.assertEqual(config["thinking_config"]["thinking_budget"], 0)

    def test_token_limit_retries_with_larger_budget(self):
        self.generate.side_effect = [
            response("未完成", "MAX_TOKENS"),
            response("【结束】完整内容。"),
        ]
        result = daily.collect_complete(
            "系统", "用户", max_tokens=320, required_markers=["【结束】"]
        )
        self.assertEqual(result, "【结束】完整内容。")
        first = self.generate.call_args_list[0].kwargs["config"].max_output_tokens
        second = self.generate.call_args_list[1].kwargs["config"].max_output_tokens
        self.assertGreater(second, first)

    def test_transient_failure_retries(self):
        self.generate.side_effect = [
            errors.ServerError(503, {"error": {"message": "Unavailable"}}),
            response(),
        ]
        self.assertEqual(daily.collect("s", "u"), "完整内容。")
        self.sleep.assert_called_once_with(30)

    def test_quota_failure_does_not_retry(self):
        self.generate.side_effect = errors.ClientError(
            429,
            {"error": {"message": "Quota exceeded", "status": "RESOURCE_EXHAUSTED"}},
        )
        with self.assertRaises(errors.ClientError):
            daily.collect("s", "u")
        self.sleep.assert_not_called()

    def test_authentication_failure_does_not_retry(self):
        self.generate.side_effect = errors.ClientError(
            400, {"error": {"message": "API key not valid"}}
        )
        with self.assertRaises(errors.ClientError):
            daily.collect("s", "u")
        self.sleep.assert_not_called()

    def test_empty_text_is_rejected(self):
        self.generate.return_value = response("")
        with self.assertRaisesRegex(RuntimeError, "no text"):
            daily.collect("s", "u")

    def test_filtered_content_is_rejected(self):
        self.generate.return_value = response("partial", "SAFETY")
        with self.assertRaisesRegex(RuntimeError, "SAFETY"):
            daily.collect("s", "u")

    def test_missing_key_is_actionable(self):
        with patch.object(daily, "client", None), patch.dict(
            os.environ, {"GEMINI_API_KEY": ""}
        ):
            with self.assertRaisesRegex(RuntimeError, "Missing GEMINI_API_KEY"):
                daily.collect("s", "u")


if __name__ == "__main__":
    unittest.main()
