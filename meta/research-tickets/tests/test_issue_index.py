"""Behavioral tests on disposable copies, never on canonical project data."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'scripts'))
import issue_index as ix
from ticket_fs import try_lock


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='research-index-')
        self.root = Path(self.temp.name).resolve()
        shutil.copytree(APP / 'tests/fixtures', self.root / 'data', ignore=shutil.ignore_patterns('history', 'import'))
        self.index = ix.IssueIndex(self.root)
        self.cache = self.root / '.cache/issues-index.json'

    def tearDown(self):
        self.temp.cleanup()

    def note(self, identifier='RES-13'):
        return self.root / 'data/issues' / (identifier.lower() + '.md')

    def edit(self, identifier='RES-13', body=None, notes=None, **changes):
        path = self.note(identifier)
        meta, old_body, old_notes = ix.parse_note(path.read_text(encoding='utf-8'), identifier)
        meta.update(changes)
        content = '---\n' + '\n'.join(k + ': ' + json.dumps(v, ensure_ascii=False) for k, v in meta.items())
        path.write_text(content + '\n---\n' + (old_body if body is None else body) + ix.MARKER + (old_notes if notes is None else notes), encoding='utf-8')

    def rels(self, mutate=None):
        path = self.root / 'data/relations.json'
        value = json.loads(path.read_text(encoding='utf-8'))
        if mutate:
            mutate(value)
            path.write_text(json.dumps(value), encoding='utf-8')
        return value

    def error(self, code, fn, *args, **kwargs):
        with self.assertRaises(ix.IndexErrorDetail) as caught:
            fn(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)
        return caught.exception

    def cli(self, *args):
        result = subprocess.run([sys.executable, '-B', str(APP / 'scripts/issues.py'), '--root', str(self.root), *args],
                                cwd=tempfile.gettempdir(), capture_output=True, text=True, timeout=15, encoding='utf-8')
        self.assertNotIn('Traceback', result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_cold_warm_and_source_preservation(self):
        original = {str(p): p.read_bytes() for p in (self.root / 'data').rglob('*') if p.is_file()}
        snapshot = self.index.refresh()
        self.assertEqual((13, 31), (len(snapshot['records']), len(snapshot['relations'])))
        self.assertEqual(13, self.index.last_stats['issue_files_read'])
        self.assertEqual(2, self.index.last_stats['json_files_read'])
        self.assertEqual(snapshot, self.index.refresh())
        self.assertTrue(self.index.last_stats['cache_reused'])
        self.assertEqual(0, self.index.last_stats['source_bytes_read'])
        self.assertEqual(original, {str(p): p.read_bytes() for p in (self.root / 'data').rglob('*') if p.is_file()})
        self.assertNotIn('body', snapshot['records']['RES-13'])

    def test_filters_duplicates_archive_and_order(self):
        self.assertEqual(12, self.index.list_issues(limit=50)['total'])
        self.assertEqual(13, self.index.list_issues(include_duplicates=True)['total'])
        self.assertEqual(['RES-13', 'RES-14'], [i['id'] for i in self.index.list_issues(kind='activity', status='Ready')['items']])
        self.edit(desk_archived=True, desk_priority=0, desk_tags=['연구'])
        self.assertEqual(11, self.index.list_issues()['total'])
        items = self.index.list_issues(include_archived=True, include_duplicates=True, limit=50)['items']
        self.assertEqual('RES-13', items[-1]['id'])
        self.assertEqual(1, self.index.list_issues(tag='연구', priority=0, parent='RES-5', include_archived=True)['total'])
        self.assertEqual(1, self.index.list_issues(status='Duplicate', include_duplicates=True)['total'])

    def test_metadata_search_unicode_and_field_selection(self):
        self.edit(desk_title='연구 ＡＢＣ lemma', desk_tags=['특이행렬'], body='## Secret\n\nnotindexedsecret\n')
        result = self.index.search('연구 abc', fields=['id', 'title'])
        self.assertEqual([{'id': 'RES-13', 'title': '연구 ＡＢＣ lemma'}], result['items'])
        self.assertEqual(1, self.index.search('특이행렬')['total'])
        self.assertEqual(0, self.index.search('notindexedsecret')['total'])

    def test_excerpt_whole_block_and_explicit_summary(self):
        self.edit(body='## Statement and scope\n\n' + 'x' * 601 + '\n')
        self.assertEqual('', self.index.refresh()['records']['RES-13']['excerpt'])
        self.edit(desk_summary='직접 작성한 범위')
        record = self.index.refresh()['records']['RES-13']
        self.assertEqual(('직접 작성한 범위', 'desk_summary'), (record['excerpt'], record['excerpt_source']))

    def test_one_changed_file_and_preserved_mtime(self):
        self.index.refresh()
        old = self.note().stat()
        self.edit(desk_priority=3)
        os.utime(self.note(), ns=(old.st_atime_ns, old.st_mtime_ns))
        self.assertEqual(3, self.index.refresh()['records']['RES-13']['priority'])
        self.assertEqual(1, self.index.last_stats['issue_files_read'])
        self.assertEqual(0, self.index.last_stats['json_files_read'])

    def test_relation_change_rebuilds_both_directions(self):
        self.index.refresh()
        key = self.rels()[0]['key']
        self.rels(lambda rels: rels[0].update({'from': 'RES-13', 'to': 'RES-14'}))
        snapshot = self.index.refresh()
        self.assertEqual(0, self.index.last_stats['issue_files_read'])
        self.assertEqual(1, self.index.last_stats['json_files_read'])
        self.assertIn(key, snapshot['adjacency']['RES-13']['outgoing'])
        self.assertIn(key, snapshot['adjacency']['RES-14']['incoming'])
        self.assertEqual(1, sum(key in adj['outgoing'] for adj in snapshot['adjacency'].values()))

    def test_parent_reassignment_and_graph_groups(self):
        self.index.refresh()
        self.edit(desk_parent='RES-6')
        snapshot = self.index.refresh()
        self.assertNotIn('contains-RES-13', snapshot['adjacency']['RES-5']['outgoing'])
        self.assertIn('contains-RES-13', snapshot['adjacency']['RES-6']['outgoing'])
        self.assertTrue(all(e['type'] != 'contains' for e in self.index.neighbors('RES-13')['items']))
        self.assertEqual('contains-RES-13', self.index.neighbors('RES-13', relation_type='contains')['items'][0]['key'])

    def test_relation_qualifiers_and_inline_self_refutation(self):
        original = next(e for e in self.rels() if e['type'] == 'refutes' and e['from'] == e['to'])
        result = self.index.neighbors(original['from'], relation_type='refutes', limit=50)
        edge = next(e for e in result['items'] if e['key'] == original['key'])
        self.assertEqual(original, {k: v for k, v in edge.items() if k != 'group'})
        self.assertEqual(1, sum(e['key'] == edge['key'] for e in result['items']))
        self.assertIn('to_inline_target', edge)

    def test_noncurrent_relation_filter(self):
        edge = self.rels()[0]
        self.rels(lambda rels: rels[0].update(status='superseded'))
        self.assertNotIn(edge['key'], [e['key'] for e in self.index.neighbors(edge['from'], limit=50)['items']])
        self.assertIn(edge['key'], [e['key'] for e in self.index.neighbors(edge['from'], include_noncurrent=True, limit=50)['items']])

    def test_project_change_and_full_validation(self):
        self.index.refresh()
        path = self.root / 'data/project.json'
        project = json.loads(path.read_text(encoding='utf-8'))
        project['name'] = 'Changed project'
        path.write_text(json.dumps(project), encoding='utf-8')
        self.assertEqual('Changed project', self.index.refresh()['project']['name'])
        self.assertEqual((0, 1), (self.index.last_stats['issue_files_read'], self.index.last_stats['json_files_read']))
        self.assertEqual(13, self.index.validate()['stats']['issue_files_read'])

    def test_add_remove_and_ignored_temporary_files(self):
        self.index.refresh()
        self.note('RES-18').write_text(self.note().read_text(encoding='utf-8').replace('desk_id: "RES-13"', 'desk_id: "RES-18"'), encoding='utf-8')
        (self.note().parent / '.res-19-random.tmp').write_text('unfinished', encoding='utf-8')
        self.assertEqual(14, len(self.index.refresh()['records']))
        self.note('RES-18').unlink()
        self.assertEqual(13, len(self.index.refresh()['records']))
        self.note('RES-5').unlink()
        self.error('DANGLING_REFERENCE', self.index.refresh)

    def test_invalid_metadata_fails_instead_of_serving_cache(self):
        cases = [dict(desk_kind=[]), dict(desk_priority=True), dict(desk_schema=True), dict(desk_status_type='bad'),
                 dict(desk_labels=[{}]), dict(desk_tags='bad'), dict(desk_archived=1), dict(desk_parent='../x'),
                 dict(desk_source_url='file:///tmp/a'), dict(desk_source_url='https://' + 'user:fixture-password@example.org'),
                 dict(desk_modified_at='bad'), dict(desk_id='RES-999'), dict(desk_summary='')]
        source = self.note().read_text(encoding='utf-8')
        self.index.refresh()
        for changes in cases:
            with self.subTest(changes=changes):
                self.note().write_text(source, encoding='utf-8')
                self.edit(**changes)
                self.error('INVALID_DATA', self.index.refresh)

    def test_invalid_encoding_duplicate_keys_and_missing_marker(self):
        source = self.note().read_bytes()
        corruptions = [b'bad', source.replace(b'desk_schema: 1', b'desk_schema: 1\ndesk_schema: 1'),
                       source.replace(b'desk_priority: 2', b'desk_priority: NaN'), source + b'\xff',
                       source.replace(b'desk_priority: 2', b'desk_priority: "\\ud800"'),
                       source.replace(ix.MARKER.encode(), b'\n'), source + ix.MARKER.encode()]
        for content in corruptions:
            with self.subTest(content=content[:30]):
                self.note().write_bytes(content)
                self.error('INVALID_DATA', self.index.refresh)
        self.note().write_bytes(source)
        (self.root / 'data/project.json').write_text('{"id":"a","id":"b"}', encoding='utf-8')
        self.error('INVALID_DATA', self.index.refresh)

    def test_dangling_parent_and_duplicate(self):
        for field in ('desk_parent', 'desk_duplicate_of'):
            with self.subTest(field=field):
                self.edit(**{field: 'RES-999'})
                self.error('DANGLING_REFERENCE', self.index.refresh)
                self.edit(**{field: None})

    def test_invalid_relations(self):
        original = self.rels()
        for field, value, code in [('to', 'RES-999', 'DANGLING_REFERENCE'), ('logic', None, 'INVALID_DATA'),
                                   ('from_version', {}, 'INVALID_DATA'), ('to_inline_target', [], 'INVALID_DATA'),
                                   ('type', 'contains', 'INVALID_DATA'), ('key', 'contains-RES-13', 'INVALID_DATA')]:
            with self.subTest(field=field):
                (self.root / 'data/relations.json').write_text(json.dumps(original), encoding='utf-8')
                self.rels(lambda rels: rels[0].update({field: value}))
                self.error(code, self.index.refresh)
        (self.root / 'data/relations.json').write_text(json.dumps(original + [original[0]]), encoding='utf-8')
        self.error('INVALID_DATA', self.index.refresh)

    def test_cache_corruption_and_version_recover(self):
        self.index.refresh()
        original = json.loads(self.cache.read_text(encoding='utf-8'))
        for corrupt in ['{broken', '[]', json.dumps(dict(original, checksum='bad')), json.dumps(dict(original, schema_version=999))]:
            with self.subTest(corrupt=corrupt[:30]):
                self.cache.write_text(corrupt, encoding='utf-8')
                self.assertEqual(13, len(self.index.refresh()['records']))
                self.assertEqual(13, self.index.last_stats['issue_files_read'])

    def test_parser_change_invalidates_cache_and_cursors(self):
        first = self.index.list_issues(limit=1)
        with patch.object(ix, 'PARSER_FINGERPRINT', 'different-implementation'):
            updated = self.index.refresh()
            self.assertEqual(13, self.index.last_stats['issue_files_read'])
            self.assertNotEqual(first['generation'], updated['generation'])
            self.error('STALE_CURSOR', self.index.list_issues, cursor=first['next_cursor'])

    def test_empty_scope_has_no_heading_excerpt(self):
        self.edit(body='## Statement and scope')
        record = self.index.refresh()['records']['RES-13']
        self.assertEqual('', record['excerpt'])
        self.assertIsNone(record['excerpt_source'])

    def test_ambiguous_scope_has_no_arbitrary_excerpt(self):
        self.edit(body='## Statement and scope\n\nfirst\n\n## Statement and scope\n\nsecond')
        record = self.index.refresh()['records']['RES-13']
        self.assertEqual('', record['excerpt'])
        self.assertIn('ambiguous_statement_and_scope', record['source_warnings'])
        self.error('AMBIGUOUS_SECTION', self.index.get_section, 'RES-13', section='Statement and scope')

    def test_real_math_excerpt_signals_omitted_scope(self):
        record = self.index.refresh()['records']['RES-7']
        self.assertTrue(record['excerpt'].endswith(':'))
        self.assertFalse(record['excerpt_scope_complete'])
        self.edit(body='## Statement and scope\n\nA complete short paragraph.')
        self.assertTrue(self.index.refresh()['records']['RES-13']['excerpt_scope_complete'])

    def test_unterminated_blocks_surface_warnings(self):
        for opener, warning in [('```tex', 'unterminated_code_fence'), ('~~~text', 'unterminated_code_fence'),
                                ('$$', 'unterminated_display_math'), ('\\[', 'unterminated_display_math')]:
            with self.subTest(opener=opener):
                self.edit(body='## Before\n\n' + opener + '\n\nx+y\n\n## Hidden\n\nnot a reliable heading\n')
                record = self.index.refresh()['records']['RES-13']
                self.assertIn(warning, record['source_warnings'])
                error = self.error('NOT_FOUND', self.index.get_section, 'RES-13', section='Hidden')
                self.assertFalse(error.details['section_scan_complete'])
                self.assertIn(warning, error.details['source_warnings'])
                self.assertIn(warning, self.index.get_section('RES-13')['source_warnings'])

    def test_indented_code_fence_does_not_hide_real_heading(self):
        self.edit(body='    ```\n    indented code\n\n## Real\n\ntext\n')
        self.assertEqual('## Real\n\ntext\n', self.index.get_section('RES-13', section='Real')['content'])

    def test_delete_unreferenced_issue_mid_scan_retries(self):
        self.note('RES-18').write_text(self.note().read_text(encoding='utf-8').replace('desk_id: "RES-13"', 'desk_id: "RES-18"'), encoding='utf-8')
        original = self.index._read
        def disappearing(path, *args):
            if path == 'data/issues/res-18.md':
                self.note('RES-18').unlink()
            return original(path, *args)
        with patch.object(self.index, '_read', side_effect=disappearing):
            snapshot = self.index.refresh()
        self.assertEqual(13, len(snapshot['records']))
        self.assertEqual(2, self.index.last_stats['attempts'])

    def test_torn_section_read_retries(self):
        self.index.refresh()
        original = self.index._read
        count = 0
        def torn(path, *args):
            nonlocal count
            if path == 'data/issues/res-13.md':
                count += 1
                if count == 1:
                    ix.fail('SOURCE_CHANGED', 'simulated torn read')
            return original(path, *args)
        with patch.object(self.index, '_read', side_effect=torn):
            self.assertTrue(self.index.get_section('RES-13', section='Statement and scope')['content'])
        self.assertEqual(2, count)

    def test_section_cursor_from_another_issue_is_invalid(self):
        self.edit(body='first\n\nsecond\n')
        cursor = self.index.get_section('RES-13', max_chars=7)['next_cursor']
        self.error('INVALID_CURSOR', self.index.get_section, 'RES-14', cursor=cursor)

    def test_cache_valid_checksum_but_invalid_shape_recovers(self):
        self.index.refresh()
        original = json.loads(self.cache.read_text(encoding='utf-8'))
        for field, value in [('manifest', []), ('records', {}), ('manifest', {'data/project.json': {}})]:
            with self.subTest(field=field, value=value):
                damaged = {k: v for k, v in original.items() if k != 'checksum'}
                damaged[field] = value
                damaged['checksum'] = ix.digest(ix.canonical(damaged))
                self.cache.write_text(json.dumps(damaged), encoding='utf-8')
                self.assertEqual(13, len(self.index.refresh()['records']))

    def test_pagination_complete_and_bounded(self):
        first = self.index.list_issues(limit=3, fields=['id'])
        results, page = [], first
        while True:
            results += page['items']
            self.assertLessEqual(page['returned'], 3)
            if not page['next_cursor']:
                break
            page = self.index.list_issues(limit=3, fields=['id'], cursor=page['next_cursor'])
        self.assertEqual(12, len(results))
        self.assertEqual(12, len({i['id'] for i in results}))
        self.error('INVALID_CURSOR', self.index.list_issues, fields=['title'], cursor=first['next_cursor'])
        self.edit(desk_priority=1)
        self.error('STALE_CURSOR', self.index.list_issues, fields=['id'], cursor=first['next_cursor'])

    def test_invalid_arguments_and_cursors(self):
        for options in [dict(limit=0), dict(limit=51), dict(limit=True), dict(priority=8), dict(kind=[]),
                        dict(status={}), dict(fields=[[]]), dict(fields=['id', 'id']), dict(fields='id'),
                        dict(tag=[]), dict(parent='../x'), dict(query=''), dict(include_archived='yes')]:
            with self.subTest(options=options):
                self.error('INVALID_ARGUMENT', self.index.list_issues, **options)
        for cursor in ('!', 'W10', 'x' * 2049):
            self.error('INVALID_CURSOR', self.index.list_issues, cursor=cursor)
        self.error('NOT_FOUND', self.index.neighbors, 'RES-999')
        self.error('INVALID_ARGUMENT', self.index.neighbors, 'RES-13', relation_type=[])
        self.error('INVALID_ARGUMENT', self.index.get_section, 'RES-13', section=[])

    def test_exact_section_and_notes(self):
        text = 'intro\n\n## Scope\n\n원문 $x$\n\n### Child\n\nchild\n\n## Next\n\nnext\n'
        self.edit(body=text, notes='개인 메모\n')
        result = self.index.get_section('RES-13', section='scope')
        self.assertEqual(text[text.index('## Scope'):text.index('## Next')], result['content'])
        self.assertEqual('개인 메모\n', self.index.get_section('RES-13', notes=True)['content'])
        self.error('NOT_FOUND', self.index.get_section, 'RES-13', section='missing')
        self.error('INVALID_ARGUMENT', self.index.get_section, 'RES-13', notes=True, section='Scope')

    def test_section_headings_ignore_fences_and_math(self):
        self.edit(body='## Real\n\n```md\n## Fake\n```\n\n$$\n## MathFake\n$$\n\n## Real\n\nagain')
        self.error('AMBIGUOUS_SECTION', self.index.get_section, 'RES-13', section='Real')
        self.error('NOT_FOUND', self.index.get_section, 'RES-13', section='Fake')
        self.error('NOT_FOUND', self.index.get_section, 'RES-13', section='MathFake')

    def test_heading_hashes_are_literal_unless_space_separated(self):
        self.edit(body='## C#\n\nfirst\n\n## Closed ###\n\nsecond\n')
        self.assertEqual('## C#\n\nfirst\n\n', self.index.get_section('RES-13', section='C#')['content'])
        self.assertEqual('## Closed ###\n\nsecond\n', self.index.get_section('RES-13', section='Closed')['content'])

    def test_empty_heading_still_ends_previous_section(self):
        self.edit(body='## Scope\n\nfirst\n\n##\n\nsecond\n')
        self.assertEqual('## Scope\n\nfirst\n\n', self.index.get_section('RES-13', section='Scope')['content'])
        self.assertEqual('##\n\nsecond\n', self.index.get_section('RES-13', section='')['content'])

    def test_json_sources_require_utf8_like_node_reader(self):
        path = self.root / 'data/project.json'
        path.write_bytes(path.read_text(encoding='utf-8').encode('utf-16'))
        self.error('INVALID_DATA', self.index.refresh)

    def test_missing_section_error_has_bounded_heading_previews(self):
        self.edit(body='## ' + 'x' * 100000 + '\n\ntext\n')
        error = self.error('NOT_FOUND', self.index.get_section, 'RES-13', section='missing')
        self.assertLess(len(json.dumps(error.details)), 6000)
        self.assertTrue(error.details['available_truncated'])

    def test_source_and_cache_size_limits_fail_without_source_writes(self):
        self.index.refresh()
        original_cache = self.cache.read_bytes()
        original_source = self.note().read_bytes()
        with patch.object(ix, 'MAX_CACHE_BYTES', 100):
            self.error('INDEX_TOO_LARGE', self.index.refresh, force=True)
        self.assertEqual(original_cache, self.cache.read_bytes())
        self.assertEqual(original_source, self.note().read_bytes())
        with self.note().open('ab') as stream:
            stream.write(b'x' * ix.MAX_FILE_BYTES)
        self.error('INVALID_DATA', self.index.refresh)

    def test_show_pagination_preserves_math_tables_code_unicode(self):
        units = ['문단 α\n\n', '$$\na+b\n\nc+d\n$$\n\n', '\\[\na\n\nb\n\\]\n\n',
                 '```tex\nx\n\ny\n```\n\n', '~~~text\nx\n\ny\n~~~\n\n', '|a|b|\n|-|-|\n|1|2|\n\n', '끝\n']
        body = ''.join(units)
        self.edit(body=body)
        page = self.index.get_section('RES-13', max_chars=max(map(len, units)))
        chunks = []
        while True:
            chunks.append(page['content'])
            if not page['next_cursor']:
                break
            page = self.index.get_section('RES-13', max_chars=max(map(len, units)), cursor=page['next_cursor'])
        self.assertEqual(body, ''.join(chunks))
        for unit in units:
            self.assertTrue(any(unit in chunk for chunk in chunks), unit)

    def test_oversized_block_and_stale_show_cursor(self):
        self.edit(body='a' * 100 + '\n\nsecond paragraph\n')
        error = self.error('BLOCK_TOO_LARGE', self.index.get_section, 'RES-13', max_chars=50)
        self.assertEqual(102, error.details['required_chars'])
        first = self.index.get_section('RES-13', max_chars=102)
        self.assertTrue(first['truncated'])
        self.edit(desk_priority=1)
        self.error('STALE_CURSOR', self.index.get_section, 'RES-13', cursor=first['next_cursor'])

    def test_concurrent_processes_build_one_valid_cache(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.cli('index', 'refresh'), range(6)))
        self.assertTrue(all(code == 0 for code, _ in results), results)
        self.assertEqual(1, len({value['generation'] for _, value in results}))
        self.assertEqual(13, sum(value['stats']['issue_files_read'] for _, value in results))
        self.assertEqual([], list(self.cache.parent.glob('*.tmp')))

    def test_killed_lock_holder_does_not_strand_lock(self):
        self.index.refresh()
        script = "import sys,time; sys.path.insert(0,sys.argv[2]); from ticket_fs import try_lock; f=open(sys.argv[1],'r+'); try_lock(f.fileno()); print('locked',flush=True); time.sleep(30)"
        process = subprocess.Popen([sys.executable, '-B', '-c', script, str(self.root / '.research-desk.lock'), str(APP / 'scripts')], stdout=subprocess.PIPE, text=True, encoding='utf-8')
        try:
            self.assertEqual('locked', process.stdout.readline().strip())
            self.error('INDEX_BUSY', ix.IssueIndex(self.root, lock_timeout=.03).refresh)
        finally:
            process.kill()
            process.wait(timeout=5)
            process.stdout.close()
        self.assertEqual(13, len(self.index.refresh()['records']))

    def test_directory_symlinks_and_project_local_cache(self):
        with tempfile.TemporaryDirectory() as other:
            second = Path(other)
            shutil.copytree(self.root / 'data', second / 'data')
            self.index.refresh()
            shutil.copytree(self.root / '.cache', second / '.cache')
            other_index = ix.IssueIndex(second)
            other_index.refresh()
            self.assertEqual(13, other_index.last_stats['issue_files_read'])
            self.assertEqual(ix.digest(str(second.resolve())), json.loads((second / '.cache/issues-index.json').read_text(encoding='utf-8'))['root'])
            (self.root / 'data/issues').rename(self.root / 'saved-issues')
            (self.root / 'data/issues').symlink_to(second / 'data/issues', target_is_directory=True)
            self.error('UNSAFE_PATH', ix.IssueIndex, self.root)

    def test_single_result_over_budget_is_explicit(self):
        self.edit(desk_tags=['x' * 200] * 100, desk_labels=['y' * 200] * 100)
        self.error('RESULT_TOO_LARGE', self.index.list_issues, tag='x' * 200, fields=['id', 'tags', 'labels'])
        self.assertEqual([{'id': 'RES-13'}], self.index.list_issues(tag='x' * 200, fields=['id'])['items'])

    def test_lock_timeout_and_release(self):
        self.index.refresh()
        with (self.root / '.research-desk.lock').open('r+') as stream:
            try_lock(stream.fileno())
            self.error('INDEX_BUSY', ix.IssueIndex(self.root, lock_timeout=.03).refresh)
        self.assertEqual(13, len(self.index.refresh()['records']))

    def test_transient_missing_lock_during_initial_creation_retries(self):
        original = ix.os.open
        attempts = 0
        def transient(path, *args, **kwargs):
            nonlocal attempts
            if Path(path).name == '.research-desk.lock':
                attempts += 1
                if attempts == 1:
                    raise FileNotFoundError(2, 'simulated concurrent lock creation')
            return original(path, *args, **kwargs)
        with patch.object(ix.os, 'open', side_effect=transient):
            self.assertEqual(13, len(self.index.refresh()['records']))
        self.assertEqual(2, attempts)

    def test_atomic_cache_replace_failure_preserves_previous(self):
        self.index.refresh()
        original = self.cache.read_bytes()
        self.edit(desk_priority=1)
        with patch.object(ix.os, 'replace', side_effect=OSError('simulated disk error')):
            with self.assertRaises(OSError):
                self.index.refresh()
        self.assertEqual(original, self.cache.read_bytes())
        self.assertEqual([], list(self.cache.parent.glob('*.tmp')))
        self.assertEqual(1, self.index.refresh()['records']['RES-13']['priority'])

    def test_source_changes_during_scan_retry_and_bounded_failure(self):
        original = self.index._inventory
        calls = 0
        def once():
            nonlocal calls
            calls += 1
            if calls == 2:
                self.edit(desk_priority=1)
            return original()
        with patch.object(self.index, '_inventory', side_effect=once):
            self.assertEqual(1, self.index.refresh()['records']['RES-13']['priority'])
        self.assertEqual(2, self.index.last_stats['attempts'])
        def always():
            nonlocal calls
            calls += 1
            self.edit(desk_title='Changed ' + str(calls))
            return original()
        with patch.object(self.index, '_inventory', side_effect=always):
            self.error('SOURCE_CHANGED', self.index.refresh)

    def test_symlinks_and_fifo_rejected(self):
        self.index.refresh()
        with tempfile.TemporaryDirectory() as external:
            outside = Path(external) / 'target'
            outside.write_text('keep unchanged', encoding='utf-8')
            for relative in ('data/issues/res-13.md', '.cache/issues-index.json', '.research-desk.lock'):
                path = self.root / relative
                saved = path.read_bytes()
                path.unlink()
                path.symlink_to(outside)
                with self.subTest(relative=relative), self.assertRaises((ix.IndexErrorDetail, OSError)):
                    self.index.refresh()
                self.assertEqual('keep unchanged', outside.read_text(encoding='utf-8'))
                path.unlink()
                path.write_bytes(saved)
            if hasattr(os, 'mkfifo'):
                fifo = self.note('RES-18')
                os.mkfifo(fifo)
                self.error('UNSAFE_PATH', self.index.refresh)
                fifo.unlink()
            cache_dir = self.root / '.cache'
            cache_dir.rename(self.root / 'saved-cache')
            cache_dir.symlink_to(external, target_is_directory=True)
            self.error('UNSAFE_PATH', self.index.refresh)
            self.assertEqual(['target'], os.listdir(external))

    def test_cli_commands_errors_and_cross_process_cursor(self):
        for args in [('index', 'rebuild'), ('validate',), ('search', 'CE'), ('neighbors', 'RES-13'), ('show', 'RES-13', '--section', 'Statement and scope')]:
            with self.subTest(args=args):
                self.assertEqual(0, self.cli(*args)[0])
        code, first = self.cli('list', '--limit', '3')
        self.assertEqual(0, code)
        code, second = self.cli('list', '--limit', '3', '--cursor', first['next_cursor'])
        self.assertEqual(0, code)
        self.assertFalse({i['id'] for i in first['items']} & {i['id'] for i in second['items']})
        for args in [('list', '--limit', 'NaN'), ('show', '../../etc/passwd'), ('list', '--unknown'), ('neighbors', 'RES-999')]:
            code, value = self.cli(*args)
            self.assertEqual(2, code)
            self.assertFalse(value['ok'])

    def test_thousand_issues_incremental_and_output_budget(self):
        source = self.note().read_text(encoding='utf-8')
        for number in range(18, 1005):
            self.note('RES-' + str(number)).write_text(source.replace('desk_id: "RES-13"', 'desk_id: "RES-' + str(number) + '"'), encoding='utf-8')
        start = time.monotonic()
        self.assertEqual(1000, len(self.index.refresh()['records']))
        cold = time.monotonic() - start
        start = time.monotonic()
        result = self.index.list_issues(limit=50)
        warm = time.monotonic() - start
        self.assertEqual(0, self.index.last_stats['source_bytes_read'])
        self.assertLessEqual(sum(len(ix.canonical(i)) for i in result['items']), ix.PAGE_BUDGET)
        self.assertTrue(result['truncated'])
        self.edit('RES-1004', desk_priority=1)
        self.index.refresh()
        self.assertEqual(1, self.index.last_stats['issue_files_read'])
        print(json.dumps({'benchmark': {'issues': 1000, 'cold_seconds': round(cold, 4), 'warm_seconds': round(warm, 4),
                                        'result_chars': len(json.dumps(result)), 'returned': result['returned']}}))


if __name__ == '__main__':
    unittest.main()
