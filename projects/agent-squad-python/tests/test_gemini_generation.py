"""Unit tests for Gemini-backed daily content generation."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
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
        self.assertEqual(call["model"], "gemini-3.1-pro-preview")
        self.assertEqual(call["contents"], "用户")
        config = call["config"].model_dump(exclude_none=True)
        self.assertEqual(config["system_instruction"], "系统")
        self.assertEqual(config["max_output_tokens"], 320)
        self.assertEqual(config["thinking_config"]["thinking_level"], "LOW")

    def test_model_override_uses_flash_without_thinking(self):
        self.generate.return_value = response()
        daily.collect("系统", "用户", model="gemini-2.5-flash")
        call = self.generate.call_args.kwargs
        self.assertEqual(call["model"], "gemini-2.5-flash")
        config = call["config"].model_dump(exclude_none=True)
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

    def test_structured_news_translations_require_every_item(self):
        raw = json.dumps([
            {"index": 1, "title_cn": "中文标题一", "summary": "完整导读一"},
            {"index": 2, "title_cn": "中文标题二", "summary": "完整导读二"},
        ])
        self.assertEqual(
            daily._parse_news_translations(raw, 2),
            {0: ("中文标题一", "完整导读一"), 1: ("中文标题二", "完整导读二")},
        )
        incomplete = json.dumps([
            {"index": 1, "title_cn": "中文标题一", "summary": "完整导读一"}
        ])
        with self.assertRaisesRegex(RuntimeError, r"item\(s\): 2"):
            daily._parse_news_translations(incomplete, 2)

    def test_expression_list_and_dialogue_are_extractable(self):
        text = """【英文原文】
A: We should play it by ear.
B：That works for me.
A: Let's check tomorrow.
B: Deal.
【中文翻译】
A：我们随机应变。
【本日表达列表】
1. **play it by ear** — 含义：随机应变 | 地区：全球通用 | 场景：计划
2. read the room — 含义：察言观色 | 地区：全球通用 | 场景：社交
"""
        self.assertEqual(
            daily._extract_english_dialogue(text).splitlines()[0],
            "A: We should play it by ear.",
        )
        self.assertEqual(
            daily._extract_expression_names(text),
            ["play it by ear", "read the room"],
        )
        self.assertEqual(
            daily._basic_expression_items(["async", "circle back", "read the room", "chock-a-block"]),
            ["async", "circle back"],
        )

    def test_dialogue_audio_uses_male_and_female_voices(self):
        inline_data = SimpleNamespace(data=b"\x00\x00" * 240)
        part = SimpleNamespace(inline_data=inline_data)
        candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]))
        self.generate.return_value = SimpleNamespace(candidates=[candidate])
        text = """【英文原文】
A: We should play it by ear.
B: That works for me.
A: Let's check tomorrow.
B: Deal.
【中文翻译】
A：我们随机应变。
"""
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            daily, "DATA_DIR", Path(temp_dir) / "data"
        ):
            audio_path = daily.gen_dialogue_audio(text, "2026-09-12")
            self.assertTrue(audio_path.exists())
        call = self.generate.call_args.kwargs
        self.assertEqual(call["model"], "gemini-2.5-pro-preview-tts")
        config = call["config"].model_dump(exclude_none=True)
        speakers = config["speech_config"]["multi_speaker_voice_config"]["speaker_voice_configs"]
        self.assertEqual([item["speaker"] for item in speakers], ["A", "B"])
        self.assertEqual(
            [item["voice_config"]["prebuilt_voice_config"]["voice_name"] for item in speakers],
            ["Puck", "Kore"],
        )


if __name__ == "__main__":
    unittest.main()
