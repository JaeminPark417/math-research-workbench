"""Synthetic output only: no model, credentials, or network are used."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
VERIFY = runpy.run_path(str(ROOT / 'scripts/review-output.py'))
MODEL = 'claude-opus-5'


def stream():
    return [
        {'type': 'system', 'subtype': 'init', 'model': MODEL, 'session_id': 'fixture',
         'tools': [], 'mcp_servers': [], 'skills': [], 'plugins': []},
        {'type': 'assistant', 'session_id': 'fixture',
         'message': {'model': MODEL, 'content': [{'type': 'text', 'text': 'First finding.'}]}},
        {'type': 'assistant', 'session_id': 'fixture',
         'message': {'model': MODEL, 'content': [{'type': 'text', 'text': 'Second finding.'}]}},
        {'type': 'result', 'subtype': 'success', 'is_error': False,
         'session_id': 'fixture', 'result': 'Second finding.', 'modelUsage': {MODEL: {}}},
    ]


class ReviewOutputTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'output.jsonl'

    def write(self, events, encoding='utf-8'):
        self.path.write_text('\n'.join(json.dumps(event) for event in events), encoding=encoding)
        return self.path

    def verify(self, events):
        return VERIFY['verify_output'](self.write(events))

    def rejects(self, events):
        with self.assertRaises((VERIFY['ReviewError'], ValueError)):
            self.verify(events)

    def test_keeps_all_findings_without_duplicate_final(self):
        result = self.verify(stream())
        self.assertEqual(result['result'], 'First finding.\n\nSecond finding.')
        self.assertEqual(result['primary_model'], MODEL)
        self.assertTrue(result['tool_free'])

    def test_final_only_and_auxiliary_haiku(self):
        events = stream()[::3]
        events[-1]['modelUsage']['claude-haiku-4-5'] = {}
        result = self.verify(events)
        self.assertEqual(result['result'], 'Second finding.')
        self.assertEqual(len(result['model_usage']), 2)

    def test_capabilities_must_be_explicit_empty_lists(self):
        for field in ('tools', 'mcp_servers', 'skills', 'plugins'):
            for value in (None, {}, '', ['Read']):
                with self.subTest(field=field, value=value):
                    events = stream()
                    events[0][field] = value
                    self.rejects(events)
            events = stream()
            del events[0][field]
            self.rejects(events)

    def test_nested_tool_and_hook_events_fail(self):
        for kind in ('tool_use', 'server_tool_use', 'tool_result', 'hook_started', 'function_call'):
            events = stream()
            events[1]['message']['content'] = [{'type': kind, 'name': 'Read'}]
            self.rejects(events)
        for field in ('tool_use_id', 'parent_tool_use_id', 'tool_calls', 'function_call'):
            events = stream()
            events[1]['nested'] = {'payload': [{field: 'fixture'}]}
            self.rejects(events)

    def test_prose_about_tools_is_not_a_tool_call(self):
        events = stream()
        events[1]['message']['content'][0]['text'] = 'Do not use tool_use or hooks.'
        self.assertTrue(self.verify(events)['tool_free'])

    def test_model_substitution_and_missing_usage_fail(self):
        for model in ('opus', 'claude-sonnet-5', 'foreign-model', None):
            events = stream()
            events[0]['model'] = model
            self.rejects(events)
        for usage in ({}, None, {'claude-haiku-4-5': {}}, {MODEL: {}, 'foreign-model': {}}):
            events = stream()
            events[-1]['modelUsage'] = usage
            self.rejects(events)
        events = stream()
        events[1]['message']['model'] = 'claude-sonnet-5'
        self.rejects(events)

    def test_malformed_success_fails(self):
        for field, value in (('is_error', True), ('is_error', 0), ('result', ''),
                             ('result', {}), ('subtype', 'error')):
            events = stream()
            events[-1][field] = value
            self.rejects(events)

    def test_incomplete_and_mixed_sessions_fail(self):
        events = stream()
        for candidate in ([], events[1:], events[:-1], events + [events[1]],
                          [events[0]] + events):
            self.rejects(candidate)
        for index in (1, -1):
            candidate = copy.deepcopy(events)
            candidate[index]['session_id'] = 'other'
            self.rejects(candidate)
        del events[-1]['session_id']
        self.rejects(events)

    def test_unknown_assistant_blocks_and_bad_json_fail(self):
        events = stream()
        events[1]['message']['content'] = [{'type': 'unknown'}]
        self.rejects(events)
        self.path.write_text('{invalid', encoding='utf-8')
        with self.assertRaises(ValueError):
            VERIFY['verify_output'](self.path)

    def test_unknown_event_types_fail_closed(self):
        for event in ({'type': 'browser_navigation'}, {'type': 'mcp_action'},
                      {'type': 'system', 'subtype': 'unknown_capability'}):
            events = stream()
            events.insert(1, event)
            self.rejects(events)

    def test_known_progress_events_remain_accepted(self):
        events = stream()
        events[1:1] = [{'type': 'system', 'subtype': 'thinking_tokens'},
                       {'type': 'rate_limit_event'}]
        self.assertTrue(self.verify(events)['tool_free'])

    def test_windows_utf8_bom(self):
        self.write(stream(), 'utf-8-sig')
        self.assertTrue(VERIFY['verify_output'](self.path)['tool_free'])

    def test_cli_failure_does_not_echo_raw_output(self):
        self.path.write_text('private-account-fixture', encoding='utf-8')
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/review-output.py'),
                                 str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr.strip(), 'review_output=unverified')

    def test_cli_success_excludes_metadata(self):
        events = stream()
        events[0]['account_fixture'] = 'private-account-fixture'
        self.write(events)
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/review-output.py'),
                                 str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('private-account-fixture', result.stdout)
        self.assertEqual(json.loads(result.stdout)['primary_model'], MODEL)


if __name__ == '__main__':
    unittest.main()
