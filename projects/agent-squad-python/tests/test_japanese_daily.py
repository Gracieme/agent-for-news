"""Offline checks for daily lesson integrity, audio and archive preservation."""
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import wave
from datetime import date, timedelta
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_site
import japanese_daily as jp
import japanese_voice as voice


def fixture(day=date(2026, 10, 29)):
    level, target = jp.lesson_plan(day)
    return {
        "level": level, "target": target, "date": day.isoformat(),
        "sentence": "水を飲みます。", "kana": "みずをのみます。",
        "tokens": [{"text": "水", "reading": "みず"}, {"text": "を"}, {"text": "飲みます", "reading": "のみます"}, {"text": "。"}],
        "translation": "喝水。", "scene": "喝水", "structure": "水（宾语）＋を（宾格助词）＋飲みます（谓语）。",
        "grammar": "を标记宾语。飲む→飲み→飲みます，为礼貌体。", "practice": "说喝茶。", "practice_answer": "お茶を飲みます。",
        "vocabulary": [{"word": "水", "reading": "みず", "meaning": "水，名词"}, {"word": "飲む", "reading": "のむ", "meaning": "喝，动词"}],
    }


def wav(seconds=2):
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(24000)
        stream.writeframes(b'\0\0' * int(24000 * seconds))
    return output.getvalue()


class JapaneseTests(unittest.TestCase):
    def test_levels_alternate_and_targets_rotate(self):
        first = date(2026, 10, 29)
        plans = [jp.lesson_plan(first + timedelta(days=i)) for i in range(20)]
        for left, right in zip(plans, plans[1:]):
            self.assertNotEqual(left[0], right[0])
        self.assertEqual(len(set(plans)), 20)

    def test_missing_reading_mismatch_and_multiple_sentences_rejected(self):
        lesson = fixture()
        jp.validate_lesson(lesson, lesson['level'], lesson['target'])
        for mutation in (
            lambda d: d['tokens'][0].update(reading=''),
            lambda d: d.update(kana='水をのみます。'),
            lambda d: d.update(sentence='水を飲みます。お茶も飲みます。'),
            lambda d: d['tokens'].append({'text': '余分'}),
            lambda d: d.update(translation=''),
        ):
            broken = copy.deepcopy(lesson)
            mutation(broken)
            with self.assertRaises(ValueError):
                jp.validate_lesson(broken, lesson['level'], lesson['target'])

    def test_render_escapes_content_and_has_real_audio_and_ruby(self):
        lesson = fixture()
        lesson['grammar'] = '<script>alert(1)</script>'
        rendered = jp.render_lesson(lesson)
        self.assertIn('<ruby>水', rendered)
        self.assertIn('&lt;script&gt;', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertEqual(rendered.count('<audio '), 2)
        self.assertIn('2026-10-29-japanese-normal.wav', rendered)
        self.assertIn('2026-10-29-japanese-slow.wav', rendered)
        self.assertIn('data-jp-loop', rendered)

    def test_tts_sends_only_sentence_and_decodes_complete_wav(self):
        import base64
        data = wav()
        with patch.object(jp, 'api_post', return_value={'steps': [{'type': 'model_output', 'content': [{'type': 'audio', 'data': base64.b64encode(data).decode()}]}]}) as request:
            self.assertEqual(jp.gen_audio('水を飲みます。', slow=True), data)
        endpoint, payload = request.call_args.args
        self.assertEqual(endpoint, 'interactions')
        content = payload['input'][0]['content'][0]
        self.assertEqual(content['text'], '水を飲みます。')
        self.assertIn('70', content['annotations'][0]['style'])
        self.assertEqual(payload['model'], jp.TTS_MODEL)
        self.assertEqual(payload['generation_config']['speech_config'], [{'voice': 'Kore'}])
        self.assertNotIn('speaker', content['annotations'][0])
        with self.assertRaises((wave.Error, EOFError)):
            jp.validate_wav(b'not a wav')

    def test_publish_is_idempotent_and_preserves_other_sections(self):
        day = date(2026, 10, 29)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / 'data'
            data.mkdir()
            entry_path = data / f'{day}.json'
            entry_path.write_text(json.dumps({'date_key': str(day), 'english': 'KEEP', 'research': 'RESEARCH'}))
            with patch.object(jp, 'WEBSITE_DIR', root), patch.object(jp, 'DATA_DIR', data), patch.object(jp, 'LESSON_DIR', root / 'japanese'), patch.object(jp, 'gen_lesson', return_value=fixture()) as generate, patch.object(jp, 'gen_audio', side_effect=[wav(2), wav(3)]) as audio, patch.object(jp, 'rebuild'):
                jp.publish_lesson(day)
                jp.publish_lesson(day)
                self.assertEqual(generate.call_count, 1)
                self.assertEqual(audio.call_count, 2)
            entry = json.loads(entry_path.read_text())
            self.assertEqual(entry['english'], 'KEEP')
            self.assertEqual(entry['research'], 'RESEARCH')
            self.assertIn('japanese', entry)
            with patch.object(build_site, 'DATA_DIR', data):
                build_site.save_entry(str(day), '日期', '周四', 'NEW', 'NEW')
            self.assertEqual(json.loads(entry_path.read_text())['japanese'], entry['japanese'])

    def test_failed_audio_does_not_publish_a_partial_lesson(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(jp, 'WEBSITE_DIR', root), patch.object(jp, 'DATA_DIR', root / 'data'), patch.object(jp, 'LESSON_DIR', root / 'japanese'), patch.object(jp, 'gen_lesson', return_value=fixture()), patch.object(jp, 'gen_audio', side_effect=RuntimeError('quota')):
                with self.assertRaisesRegex(RuntimeError, 'quota'):
                    jp.publish_lesson(date(2026, 10, 29))
            self.assertFalse((root / 'data' / '2026-10-29.json').exists())

    def test_rejected_teacher_review_retries_and_never_publishes(self):
        with patch.object(jp, 'recent_sentences', return_value=[]), patch.object(jp, 'generate_json', side_effect=[fixture(), {'approved': False, 'issues': '读音错误'}] * 3):
            with self.assertRaisesRegex(RuntimeError, '读音错误'):
                jp.gen_lesson(date(2026, 10, 29))

    def test_elevenlabs_upgrade_reuses_sentence_and_replaces_both_tracks(self):
        day = date(2026, 10, 29)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'japanese').mkdir()
            (root / 'audio').mkdir()
            lesson_path = root / 'japanese' / f'{day}.json'
            lesson_path.write_text(json.dumps(fixture()))
            for speed in ('normal', 'slow'):
                (root / 'audio' / f'{day}-japanese-{speed}.wav').write_bytes(wav(1 if speed == 'normal' else 2))
            metadata = {'tts_provider': 'elevenlabs', 'tts_model': 'eleven_v4', 'tts_voice_id': 'JapaneseVoice'}
            with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test', 'ELEVENLABS_MODEL': 'eleven_v4', 'ELEVENLABS_JAPANESE_VOICE_ID': ''}), patch.object(jp, 'WEBSITE_DIR', root), patch.object(jp, 'DATA_DIR', root / 'data'), patch.object(jp, 'LESSON_DIR', root / 'japanese'), patch.object(jp, 'elevenlabs_audio_pair', return_value=(wav(2), wav(3), metadata)) as generate, patch.object(jp, 'gen_audio') as gemini, patch.object(jp, 'rebuild'):
                jp.publish_lesson(day)
                jp.publish_lesson(day)
                generate.assert_called_once_with(fixture()['sentence'])
                gemini.assert_not_called()
            saved = json.loads(lesson_path.read_text())
            self.assertEqual(saved['tts_provider'], 'elevenlabs')
            self.assertEqual(saved['sentence'], fixture()['sentence'])
            entry = json.loads((root / 'data' / f'{day}.json').read_text())
            self.assertIn('?v=' + saved['audio_revision'], entry['japanese'])

    def test_elevenlabs_failure_keeps_working_pair(self):
        day = date(2026, 10, 29)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'japanese').mkdir()
            (root / 'audio').mkdir()
            (root / 'japanese' / f'{day}.json').write_text(json.dumps(fixture()))
            originals = {}
            for speed in ('normal', 'slow'):
                path = root / 'audio' / f'{day}-japanese-{speed}.wav'
                originals[path] = wav(2 if speed == 'normal' else 3)
                path.write_bytes(originals[path])
            with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test'}), patch.object(jp, 'WEBSITE_DIR', root), patch.object(jp, 'DATA_DIR', root / 'data'), patch.object(jp, 'LESSON_DIR', root / 'japanese'), patch.object(jp, 'elevenlabs_audio_pair', side_effect=RuntimeError('HTTP 401')), patch.object(jp, 'gen_audio') as gemini, patch.object(jp, 'rebuild'):
                jp.publish_lesson(day)
                gemini.assert_not_called()
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)
            self.assertNotEqual(json.loads((root / 'japanese' / f'{day}.json').read_text()).get('tts_provider'), 'elevenlabs')

    def test_voice_selection_uses_japanese_library_and_excludes_private_clones(self):
        voices = {'voices': [
            {'voice_id': 'private', 'category': 'cloned'},
            {'voice_id': 'public', 'category': 'professional', 'sharing': {'status': 'enabled'}, 'labels': {'use_case': 'conversational'}},
        ]}
        with patch.dict(os.environ, {'ELEVENLABS_JAPANESE_VOICE_ID': ''}), patch.object(voice, 'request', return_value=json.dumps(voices).encode()) as request:
            self.assertEqual(voice.select_voice(), 'public')
            self.assertIn('language=ja', request.call_args.args[0])
        with patch.dict(os.environ, {'ELEVENLABS_JAPANESE_VOICE_ID': ''}), patch.object(voice, 'request', return_value=b'{"voices": []}'):
            with self.assertRaisesRegex(RuntimeError, 'Japanese native-speaker'):
                voice.select_voice()

    def test_elevenlabs_v4_request_and_slow_track_use_same_performance(self):
        with patch.object(voice, 'select_voice', return_value='JapaneseVoice'), patch.object(voice, 'request', return_value=b'mp3') as request, patch.object(voice, 'convert_audio', side_effect=[wav(2), wav(3)]) as convert:
            normal, slow, metadata = voice.generate_pair('水を飲みます。')
            endpoint, payload = request.call_args.args
            self.assertIn('JapaneseVoice', endpoint)
            self.assertEqual(payload['language_code'], 'ja')
            self.assertEqual(payload['text'], '水を飲みます。')
            self.assertNotIn('speed', payload['voice_settings'])
            self.assertEqual(convert.call_args_list[1].args[0], normal)
            self.assertTrue(convert.call_args_list[1].kwargs['slow'])
            self.assertEqual(metadata['tts_provider'], 'elevenlabs')

    @unittest.skipUnless(__import__('shutil').which('ffmpeg'), 'ffmpeg not installed')
    def test_real_pitch_preserving_slow_conversion(self):
        import math
        import struct
        data = io.BytesIO()
        with wave.open(data, 'wb') as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(24000)
            stream.writeframes(b''.join(struct.pack('<h', int(8000 * math.sin(2 * math.pi * 440 * i / 24000))) for i in range(48000)))
        slow = voice.convert_audio(data.getvalue(), slow=True)
        duration = jp.validate_wav(slow)
        self.assertGreater(duration, 2.4)
        self.assertLess(duration, 2.7)
        with wave.open(io.BytesIO(slow)) as stream:
            samples = struct.unpack('<' + 'h' * stream.getnframes(), stream.readframes(stream.getnframes()))
        crossings = sum(left <= 0 < right for left, right in zip(samples, samples[1:]))
        self.assertAlmostEqual(crossings / duration, 440, delta=5)


if __name__ == '__main__':
    unittest.main()
