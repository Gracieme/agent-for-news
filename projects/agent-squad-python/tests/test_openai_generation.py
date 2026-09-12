"""Exercise the real OpenAI SDK against a local fake HTTP transport."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import httpx
import openai

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_email as daily


def response(text='完整内容。', status='completed', reason=None):
    return {
        'id': 'resp_test', 'object': 'response', 'created_at': 0,
        'model': 'gpt-5-mini', 'status': status,
        'incomplete_details': {'reason': reason} if reason else None,
        'output': [{'type': 'message', 'id': 'msg_test', 'role': 'assistant',
                    'status': 'completed', 'content': [{'type': 'output_text',
                    'text': text, 'annotations': []}]}],
    }


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.replies = []
        def handle(request):
            self.requests.append(json.loads(request.content))
            status, body = self.replies.pop(0)
            return httpx.Response(status, json=body)
        self.client = openai.OpenAI(api_key='test-only', max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handle)))
        self.client_patch = patch.object(daily, 'client', self.client)
        self.client_patch.start()
        self.sleep_patch = patch.object(daily.time, 'sleep')
        self.sleep = self.sleep_patch.start()

    def tearDown(self):
        self.sleep_patch.stop()
        self.client_patch.stop()
        self.client.close()

    def test_request_and_text(self):
        self.replies = [(200, response())]
        self.assertEqual(daily.collect('系统', '用户', max_tokens=320), '完整内容。')
        payload = self.requests[0]
        self.assertEqual(payload['instructions'], '系统')
        self.assertEqual(payload['input'], '用户')
        self.assertEqual(payload['max_output_tokens'], 4416)
        self.assertFalse(payload['store'])

    def test_token_limit_retries_with_larger_budget(self):
        self.replies = [(200, response('未完成', 'incomplete', 'max_output_tokens')),
                        (200, response('【结束】完整内容。'))]
        result = daily.collect_complete('系统', '用户', max_tokens=320,
                                         required_markers=['【结束】'])
        self.assertEqual(result, '【结束】完整内容。')
        self.assertGreater(self.requests[1]['max_output_tokens'],
                           self.requests[0]['max_output_tokens'])

    def test_transient_failure_retries(self):
        self.replies = [(503, {'error': {'message': 'Unavailable', 'type': 'server_error'}}),
                        (200, response())]
        self.assertEqual(daily.collect('s', 'u'), '完整内容。')
        self.sleep.assert_called_once_with(30)

    def test_quota_failure_does_not_retry(self):
        self.replies = [(429, {'error': {'message': 'Quota exhausted',
                         'type': 'insufficient_quota', 'code': 'insufficient_quota'}})]
        with self.assertRaises(openai.RateLimitError):
            daily.collect('s', 'u')
        self.sleep.assert_not_called()

    def test_credit_balance_exhausted_does_not_retry(self):
        self.replies = [(429, {'error': {'message': 'No credits remaining',
                         'type': 'insufficient_quota', 'code': 'credit_balance_exhausted'}})]
        with self.assertRaises(openai.RateLimitError):
            daily.collect('s', 'u')
        self.sleep.assert_not_called()

    def test_authentication_failure_does_not_retry(self):
        self.replies = [(401, {'error': {'message': 'Invalid key', 'type': 'invalid_request_error'}})]
        with self.assertRaises(openai.AuthenticationError):
            daily.collect('s', 'u')
        self.sleep.assert_not_called()

    def test_empty_text_is_rejected(self):
        self.replies = [(200, response(''))]
        with self.assertRaisesRegex(RuntimeError, 'no text'):
            daily.collect('s', 'u')

    def test_filtered_content_is_rejected(self):
        self.replies = [(200, response('partial', 'incomplete', 'content_filter'))]
        with self.assertRaisesRegex(RuntimeError, 'content_filter'):
            daily.collect('s', 'u')

    def test_missing_key_is_actionable(self):
        with patch.object(daily, 'client', None), patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with self.assertRaisesRegex(RuntimeError, 'Missing OPENAI_API_KEY'):
                daily.collect('s', 'u')


if __name__ == '__main__':
    unittest.main()
