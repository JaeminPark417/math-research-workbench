"""Read-only research queries over Markdown, with a disposable JSON index.

Python 3.9+, standard library only. Canonical issue/relation files are never written.
The cache lock coordinates index builders, not external Markdown editors.
"""
from __future__ import annotations

import base64
import contextlib
import copy
import datetime as dt
import ticket_fs as fs
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time
import unicodedata
from urllib.parse import urlsplit

SCHEMA = 5
HASH_INVENTORY = os.name == "nt"  # Windows st_ctime is creation time, not change time.
MARKER = '\n\n<!-- research-desk:local-notes -->\n'
FILE_RE = re.compile(r'res-[0-9]+\.md\Z')
ID_RE = re.compile(r'RES-[0-9]+\Z')
RESEARCH_KINDS = {'question', 'hypothesis', 'experiment', 'result', 'analysis', 'decision'}
KINDS = {'theorem', 'lemma', 'obligation', 'activity', 'counterexample', 'obstruction'} | RESEARCH_KINDS
OUTCOMES = {'positive', 'negative', 'null', 'mixed', 'inconclusive', 'invalid'}
STATUS_TYPES = {'Backlog': 'backlog', 'Ready': 'unstarted', 'Todo': 'unstarted',
                'In Progress': 'started', 'In Review': 'started', 'Done': 'completed',
                'Canceled': 'canceled', 'Duplicate': 'duplicate'}
RELATION_TYPES = {'requires-input-to', 'sufficient-route-to', 'refutes',
                  'useful-for', 'reviews', 'related', 'contains',
                  'tests', 'produces', 'supports', 'challenges', 'interprets',
                  'informs', 'motivates'}
EXPERIMENT_RELATION_KINDS = {
    'tests': ({'experiment'}, {'hypothesis', 'question'}),
    'produces': ({'experiment', 'activity'}, {'result'}),
    'supports': ({'result', 'analysis'}, {'hypothesis'}),
    'challenges': ({'result', 'analysis'}, {'hypothesis'}),
    'interprets': ({'analysis'}, {'result'}),
    'informs': ({'result', 'analysis'}, {'decision'}),
    'motivates': ({'decision'}, {'question', 'hypothesis', 'experiment', 'activity'}),
}
DEFAULT_FIELDS = ('id', 'title', 'kind', 'status', 'priority', 'parent', 'excerpt',
                  'excerpt_scope_complete', 'source_warnings')
FIELDS = set(DEFAULT_FIELDS) | {'labels', 'tags', 'archived', 'duplicate_of', 'path',
                              'source_url', 'modified_at', 'source_hash', 'excerpt_source',
                              'origin', 'integration_key', 'body_hash', 'blocked_by',
                              'next_action', 'priority_rationale', 'claim_ref', 'proposals',
                              'statement_role', 'source_refs', 'outcome'}
RELATION_STATUSES = {'current', 'superseded', 'needs-review', 'retracted'}
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_CACHE_BYTES = 32 * 1024 * 1024
PAGE_BUDGET = 24000
MAX_SECTION_CHARS = 100000


class IndexErrorDetail(Exception):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code, self.details = code, details


def fail(code, message, **details):
    raise IndexErrorDetail(code, message, **details)


def normalize_tags(tag):
    """One legacy tag or up to twenty AND filters; order is not semantic."""
    if tag is None:
        return []
    tags = [tag] if isinstance(tag, str) else tag
    if not isinstance(tags, list) or not 1 <= len(tags) <= 20 or any(not _text(v, 200) for v in tags):
        fail('INVALID_ARGUMENT', 'Supply one tag or a nonempty list of at most twenty tags.')
    return sorted(set(tags))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


# Bind cached derivations to the implementation loaded by this Python process.
PARSER_FINGERPRINT = digest(b''.join(p.read_bytes() for p in
    [Path(__file__).with_name(name) for name in ('issue_index.py', 'issue_store.py', 'issue_transaction.py', 'issue_sources.py', 'ticket_project.py', 'ticket_fs.py')]
    if p.exists()))


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out


def json_read(raw, label):
    try:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        value = json.loads(raw, object_pairs_hook=_unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON')))
        # JSON escape sequences can otherwise smuggle lone Unicode surrogates.
        canonical(value).encode('utf-8')
        return value
    except (ValueError, UnicodeError, RecursionError):
        fail('INVALID_DATA', 'Invalid UTF-8 JSON.', path=label)


def _text(value, limit=4096):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _web_url(value):
    try:
        u = urlsplit(value)
        return isinstance(value, str) and u.scheme in ('http', 'https') and bool(u.netloc) and not u.username and not u.password
    except (ValueError, TypeError, AttributeError):
        return False


def _timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def _id(value):
    return isinstance(value, str) and ID_RE.fullmatch(value) is not None


def validate_source_refs(value):
    """Validate bounded evidence references without opening their source files."""
    if not isinstance(value, list) or len(value) > 20:
        fail('INVALID_DATA', 'Source references must be a list of at most 20 distinct references.')
    from issue_sources import validate_reference
    result, seen = [], set()
    for entry in value:
        ref = validate_reference(entry)
        key = canonical(ref)
        if key in seen:
            fail('INVALID_DATA', 'Source references must be distinct.')
        seen.add(key)
        result.append(ref)
    return result


def validate_outcome(value, kind):
    """Outcomes describe empirical findings, independently of work-item status."""
    if value is not None and (not isinstance(value, str) or value not in OUTCOMES
                              or kind not in ('result', 'analysis')):
        fail('INVALID_DATA', 'Outcome requires a result or analysis and a supported value.')
    return value


def _statement_role(kind, claim_ref):
    if claim_ref:
        return 'canonical-reference'
    if kind == 'activity':
        return 'operational'
    return 'research-record' if kind in RESEARCH_KINDS else 'proposed'


def parse_note(raw, identifier):
    """Parse the existing desk_schema=1 JSON-valued frontmatter without YAML coercion."""
    # Parse Windows text edits without changing byte-exact source hashes.
    raw = raw.replace("\r\n", "\n")
    if not raw.startswith('---\n'):
        fail('INVALID_DATA', 'Missing frontmatter.', id=identifier)
    end = raw.find('\n---\n', 4)
    if end < 0:
        fail('INVALID_DATA', 'Unterminated frontmatter.', id=identifier)
    meta = {}
    for line in raw[4:end].split('\n'):
        match = re.fullmatch(r'([a-z_]+): (.*)', line)
        if not match or match[1] in meta:
            fail('INVALID_DATA', 'Invalid or duplicate frontmatter field.', id=identifier)
        meta[match[1]] = json_read(match[2], identifier + ':' + match[1])
    required = ('desk_schema', 'desk_id', 'desk_title', 'desk_kind', 'desk_labels',
                'desk_status', 'desk_status_type', 'desk_priority', 'desk_parent',
                'desk_duplicate_of', 'desk_archived', 'desk_source_url',
                'desk_modified_at')
    if any(k not in meta for k in required):
        fail('INVALID_DATA', 'Required issue metadata is missing.', id=identifier)
    if type(meta['desk_schema']) is not int or meta['desk_schema'] not in (1, 2) or meta['desk_id'] != identifier:
        fail('INVALID_DATA', 'Schema or filename/ID mismatch.', id=identifier)
    if not _text(meta['desk_title'], 1000) or not isinstance(meta['desk_kind'], str) or meta['desk_kind'] not in KINDS:
        fail('INVALID_DATA', 'Invalid title or kind.', id=identifier)
    for field in ('desk_labels', 'desk_tags'):
        values = meta.get(field, [])
        if not isinstance(values, list) or len(values) > 100 or any(not _text(x, 200) for x in values):
            fail('INVALID_DATA', 'Invalid labels/tags.', id=identifier)
    if not isinstance(meta['desk_status'], str) or meta['desk_status'] not in STATUS_TYPES or meta['desk_status_type'] != STATUS_TYPES[meta['desk_status']]:
        fail('INVALID_DATA', 'Status and status type disagree.', id=identifier)
    if type(meta['desk_priority']) is not int or not 0 <= meta['desk_priority'] <= 4 or type(meta['desk_archived']) is not bool:
        fail('INVALID_DATA', 'Invalid priority or archived flag.', id=identifier)
    if any(v is not None and not _id(v) for v in (meta['desk_parent'], meta['desk_duplicate_of'])):
        fail('INVALID_DATA', 'Invalid parent or duplicate identifier.', id=identifier)
    local = meta['desk_schema'] == 2 and meta.get('desk_origin') == 'local'
    if meta['desk_schema'] == 2 and not local:
        fail('INVALID_DATA', 'Schema 2 requires explicit local origin.', id=identifier)
    if not (local and meta['desk_source_url'] is None or _web_url(meta['desk_source_url'])) or not _timestamp(meta['desk_modified_at']):
        fail('INVALID_DATA', 'Invalid source URL or timestamp.', id=identifier)
    if local:
        if not _timestamp(meta.get('desk_created_at')) or any(meta.get(k) is not None for k in ('desk_imported_at', 'desk_origin_updated_at')):
            fail('INVALID_DATA', 'Local issues need creation time, not fabricated import timestamps.', id=identifier)
    elif not all(_timestamp(meta.get(k)) for k in ('desk_imported_at', 'desk_origin_updated_at')):
        fail('INVALID_DATA', 'Imported issue provenance timestamps are required.', id=identifier)
    for key in ('desk_key', 'desk_next_action', 'desk_priority_rationale'):
        if key in meta and not _text(meta[key], 2000):
            fail('INVALID_DATA', 'Invalid optional issue metadata.', id=identifier, field=key)
    blocked = meta.get('desk_blocked_by', [])
    if not isinstance(blocked, list) or len(blocked) > 100 or any(not _id(v) for v in blocked) or len(set(blocked)) != len(blocked):
        fail('INVALID_DATA', 'Invalid operational blockers.', id=identifier)
    if 'desk_summary' in meta and not _text(meta['desk_summary'], 2000):
        fail('INVALID_DATA', 'desk_summary must be a nonempty string of at most 2000 characters.', id=identifier)
    validate_source_refs(meta.get('desk_source_refs', []))
    validate_outcome(meta.get('desk_outcome'), meta['desk_kind'])
    if meta.get('desk_claim_ref') is not None:
        from issue_sources import validate_reference
        validate_reference(meta['desk_claim_ref'])
        if not _text(meta['desk_claim_ref'].get('object_id'), 200):
            fail('INVALID_DATA', 'A claim binding needs its canonical stable object ID.')
    proposals = meta.get('desk_proposals', [])
    if not isinstance(proposals, list) or len(proposals) > 100:
        fail('INVALID_DATA', 'Invalid proposal ledger.')
    keys = set()
    for p in proposals:
        if not isinstance(p, dict) or set(p) != {'key', 'status', 'statement', 'reason', 'at', 'base_ref'} or p['status'] != 'proposed' or not _text(p['key'], 64) or p['key'] in keys or not _text(p['statement'], 100000) or not _text(p['reason'], 2000) or not _timestamp(p['at']):
            fail('INVALID_DATA', 'Proposals must be distinct, dated, pending changes.')
        keys.add(p['key'])
        if p['base_ref'] is not None:
            from issue_sources import validate_reference
            validate_reference(p['base_ref'])
    rest = raw[end + 5:]
    if rest.count(MARKER) != 1:
        fail('INVALID_DATA', 'Expected exactly one local-notes marker.', id=identifier)
    body, notes = rest.split(MARKER)
    return meta, body, notes


def blocks(text, diagnostics=None):
    """Conservative source spans: never split paragraphs, tables, fences or display math."""
    spans, start, offset = [], 0, 0
    fence = None
    math_close = None
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if fence:
            if re.fullmatch(' {0,3}' + re.escape(fence[0]) + '{' + str(fence[1]) + ',}[ \t]*', line.rstrip('\r\n')):
                fence = None
        elif math_close:
            if stripped == math_close:
                math_close = None
        else:
            match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
            if match:
                fence = (match[1][0], len(match[1]))
            elif stripped in ('$$', '\\['):
                math_close = '$$' if stripped == '$$' else '\\]'
        offset += len(line)
        if not stripped and not fence and not math_close:
            if text[start:offset].strip():
                spans.append((start, offset))
                start = offset
    if start < len(text):
        spans.append((start, len(text)))
    if diagnostics is not None:
        if fence:
            diagnostics.append('unterminated_code_fence')
        if math_close:
            diagnostics.append('unterminated_display_math')
    return spans


def sections(text, diagnostics=None):
    """ATX headings outside code fences and multiline math; duplicates stay distinct."""
    headings, offset = [], 0
    fence, math_close = None, None
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if fence:
            if re.fullmatch(' {0,3}' + re.escape(fence[0]) + '{' + str(fence[1]) + ',}[ \t]*', line.rstrip('\r\n')):
                fence = None
        elif math_close:
            if stripped == math_close:
                math_close = None
        else:
            match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
            if match:
                fence = (match[1][0], len(match[1]))
            elif stripped in ('$$', '\\['):
                math_close = '$$' if stripped == '$$' else '\\]'
            else:
                heading = re.match(r'^ {0,3}(#{1,6})(?:[ \t]+(.*))?$', line.rstrip('\r\n'))
                if heading:
                    name = heading[2] or ''
                    name = '' if re.fullmatch(r'#+[ \t]*', name) else re.sub(r'[ \t]+#+[ \t]*$', '', name).strip()
                    headings.append((name, len(heading[1]), offset))
        offset += len(line)
    result = []
    for n, (name, level, start) in enumerate(headings):
        end = next((pos for _, depth, pos in headings[n + 1:] if depth <= level), len(text))
        result.append({'name': name, 'start': start, 'end': end})
    if diagnostics is not None:
        if fence:
            diagnostics.append('unterminated_code_fence')
        if math_close:
            diagnostics.append('unterminated_display_math')
    return result


def record(raw, identifier, path):
    try:
        meta, body, _ = parse_note(raw.decode('utf-8'), identifier)
    except UnicodeError:
        fail('INVALID_DATA', 'Issue must use UTF-8.', id=identifier)
    excerpt, origin, complete = '', None, None
    warnings = []
    scopes = [s for s in sections(body, warnings) if s['name'].casefold() == 'statement and scope']
    if len(scopes) > 1:
        warnings.append('ambiguous_statement_and_scope')
    if 'desk_summary' in meta:
        excerpt, origin = meta['desk_summary'], 'desk_summary'
    else:
        scope = scopes[0] if len(scopes) == 1 else None
        if scope:
            text = body[scope['start']:scope['end']].partition('\n')[2].strip()
            spans = blocks(text)
            # Only use a complete short block: no misleading partial formula/claim summaries.
            if spans and len(text[slice(*spans[0])].strip()) <= 600:
                excerpt, origin = text[slice(*spans[0])].strip(), 'Statement and scope (verbatim block)'
                complete = spans[0][1] == len(text) and not warnings
    return {'id': identifier, 'title': meta['desk_title'], 'kind': meta['desk_kind'],
            'labels': meta['desk_labels'], 'tags': meta.get('desk_tags', []),
            'status': meta['desk_status'], 'priority': meta['desk_priority'],
            'parent': meta['desk_parent'], 'duplicate_of': meta['desk_duplicate_of'],
            'archived': meta['desk_archived'], 'source_url': meta['desk_source_url'],
            'modified_at': meta['desk_modified_at'], 'path': path, 'source_hash': digest(raw),
            'excerpt': excerpt, 'excerpt_source': origin,
            'excerpt_scope_complete': complete, 'source_warnings': warnings,
            'origin': 'local' if meta['desk_schema'] == 2 else 'imported',
            'integration_key': meta.get('desk_key'), 'body_hash': digest(body),
            'blocked_by': meta.get('desk_blocked_by', []),
            'next_action': meta.get('desk_next_action'), 'priority_rationale': meta.get('desk_priority_rationale'),
            'claim_ref': meta.get('desk_claim_ref'), 'proposals': meta.get('desk_proposals', []),
            'source_refs': meta.get('desk_source_refs', []), 'outcome': meta.get('desk_outcome'),
            'statement_role': _statement_role(meta['desk_kind'], meta.get('desk_claim_ref'))}


def relation_graph(records, raw_relations):
    if not isinstance(raw_relations, list):
        fail('INVALID_DATA', 'relations.json must contain an array.')
    ids, keys, edges = set(records), set(), []
    for item in records.values():
        for name in ('parent', 'duplicate_of'):
            if item[name] is not None and item[name] not in ids:
                fail('DANGLING_REFERENCE', 'Issue reference has no target.', id=item['id'], field=name, target=item[name])
        for target in item['blocked_by']:
            if target not in ids or records[target]['kind'] != 'activity' or item['kind'] != 'activity' or target == item['id']:
                fail('INVALID_DATA', 'Operational blockers must reference other activities.', id=item['id'])
        if item['parent']:
            edges.append({'key': 'contains-' + item['id'], 'from': item['parent'], 'to': item['id'],
                          'type': 'contains', 'group': 'administrative', 'status': 'current',
                          'logic': 'organization only', 'evidence': 'Local parent metadata'})
    for rel in raw_relations:
        if not isinstance(rel, dict) or any(not _text(rel.get(k)) for k in ('key', 'type', 'status', 'logic', 'evidence')):
            fail('INVALID_DATA', 'Relation lacks required qualifiers.')
        if rel['key'] in keys or rel['key'].startswith('contains-') or rel['type'] not in RELATION_TYPES - {'contains'} or rel['status'] not in RELATION_STATUSES:
            fail('INVALID_DATA', 'Duplicate relation key or unsupported relation type.', key=rel['key'])
        keys.add(rel['key'])
        if any(not _id(rel.get(side)) or rel[side] not in ids for side in ('from', 'to')):
            fail('DANGLING_REFERENCE', 'Relation endpoint has no issue.', key=rel['key'])
        if rel['type'] in EXPERIMENT_RELATION_KINDS:
            allowed_from, allowed_to = EXPERIMENT_RELATION_KINDS[rel['type']]
            if records[rel['from']]['kind'] not in allowed_from or records[rel['to']]['kind'] not in allowed_to:
                fail('INVALID_DATA', 'Experimental relation endpoint kinds do not match its meaning.', key=rel['key'])
        for side in ('from', 'to'):
            inline, version = rel.get(side + '_inline_target'), rel.get(side + '_version')
            if inline is not None and not _text(inline):
                fail('INVALID_DATA', 'Invalid inline statement target.', key=rel['key'])
            local = isinstance(version, dict) and version.get('origin') == 'local'
            required = ('path', 'heading', 'sha256') if local else ('commit', 'path', 'heading')
            if not isinstance(version, dict) or any(not _text(version.get(k)) for k in required):
                fail('INVALID_DATA', 'Missing endpoint source version.', key=rel['key'])
            if local and (version['path'] != records[rel[side]]['path'] or not re.fullmatch('[0-9a-f]{64}', version['sha256'])):
                fail('INVALID_DATA', 'Invalid local endpoint version.', key=rel['key'])
            if local and version.get('claim_ref') is not None:
                from issue_sources import validate_reference
                validate_reference(version['claim_ref'])
            validate_source_refs(version.get('source_refs', []))
            validate_outcome(version.get('outcome'), records[rel[side]]['kind'])
        edge = copy.deepcopy(rel)
        edge['group'] = 'research'
        if edge['status'] == 'current' and any(
                edge[side + '_version'].get('origin') == 'local' and (
                    edge[side + '_version']['sha256'] != records[edge[side]]['body_hash']
                    or edge[side + '_version'].get('claim_ref') != records[edge[side]]['claim_ref']
                    or edge[side + '_version'].get('source_refs', []) != records[edge[side]]['source_refs']
                    or edge[side + '_version'].get('outcome') != records[edge[side]]['outcome'])
                for side in ('from', 'to')):
            edge['status'] = 'needs-review'
            edge['stale_reason'] = 'Local endpoint body, bound source, evidence references or outcome changed after this relation was recorded.'
        edges.append(edge)
    for field in ('parent', 'duplicate_of'):
        for identifier in ids:
            seen, current = set(), identifier
            while current is not None:
                if current in seen:
                    fail('INVALID_DATA', 'Cyclic issue hierarchy/duplicate chain.', id=identifier, field=field)
                seen.add(current)
                current = records[current][field]
    # Operational dependencies must be a DAG, independently of research edges.
    visited = set()
    for identifier in ids:
        stack, active = [(identifier, False)], set()
        while stack:
            current, leaving = stack.pop()
            if leaving:
                active.remove(current)
                visited.add(current)
            elif current in active:
                fail('INVALID_DATA', 'Cyclic operational blockers.', id=current)
            elif current not in visited:
                active.add(current)
                stack.append((current, True))
                stack.extend((target, False) for target in records[current]['blocked_by'])
    # Rebuild both directions from the entire record set, even for a one-file change.
    edges.sort(key=lambda e: e['key'])
    adjacency = {i: {'incoming': [], 'outgoing': []} for i in records}
    for edge in edges:
        adjacency[edge['from']]['outgoing'].append(edge['key'])
        adjacency[edge['to']]['incoming'].append(edge['key'])
    return edges, adjacency


def _signature(s):
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def _cursor_encode(generation, query, offset):
    return base64.urlsafe_b64encode(canonical({'g': generation, 'q': digest(canonical(query)), 'o': offset}).encode()).decode().rstrip('=')


def _cursor_offset(cursor, generation, query):
    if cursor is None:
        return 0
    try:
        if not isinstance(cursor, str) or len(cursor) > 2048:
            raise ValueError()
        value = json.loads(base64.b64decode(cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True))
        if not isinstance(value, dict) or type(value.get('o')) is not int or value['o'] < 0:
            raise ValueError()
    except (ValueError, UnicodeError, TypeError, RecursionError):
        fail('INVALID_CURSOR', 'Cursor is malformed.')
    if value.get('q') != digest(canonical(query)):
        fail('INVALID_CURSOR', 'Cursor belongs to another query.')
    if value.get('g') != generation:
        fail('STALE_CURSOR', 'Sources or index implementation changed; start a new query.')
    return value['o']


def _page(items, snapshot, query, limit, cursor):
    if type(limit) is not int or not 1 <= limit <= 50:
        fail('INVALID_ARGUMENT', 'limit must be between 1 and 50.')
    start = _cursor_offset(cursor, snapshot['generation'], query)
    if start > len(items):
        fail('INVALID_CURSOR', 'Cursor is past the end of the result.')
    page, size = [], 0
    for item in items[start:start + limit]:
        chars = len(canonical(item))
        if size + chars > PAGE_BUDGET:
            if not page:
                fail('RESULT_TOO_LARGE', 'A complete result exceeds the output budget; select fewer fields if supported, or inspect the source file.', required_chars=chars)
            break
        page.append(item)
        size += chars
    end = start + len(page)
    return {'ok': True, 'generation': snapshot['generation'], 'total': len(items),
            'returned': len(page), 'truncated': end < len(items), 'items': page,
            'next_cursor': _cursor_encode(snapshot['generation'], query, end) if end < len(items) else None,
            'freshness': 'inventory+stat/ctime (Windows: content hashes); use validate for full verification'}


class IssueIndex:
    def __init__(self, root, lock_timeout=3.0):
        root = Path(root).absolute()
        if fs.is_link(root.lstat()):
            fail('UNSAFE_PATH', 'Project root must not be a symbolic link.')
        self.root = root.resolve(strict=True)
        self.lock_timeout = lock_timeout
        self.last_stats = {}
        self._inventory_bytes_read = 0
        self._checked('data', directory=True)
        self._checked('data/issues', directory=True)

    def _checked(self, relative, directory=False):
        path = self.root / relative
        parts = Path(relative).parts
        if not parts or any(p in ('.', '..') for p in parts) or Path(relative).is_absolute():
            fail('UNSAFE_PATH', 'Path must remain in the project.')
        cursor = self.root
        for part in parts:
            cursor = cursor / part
            info = cursor.lstat()
            if fs.is_link(info):
                fail('UNSAFE_PATH', 'Symbolic links are not accepted.', path=relative)
        info = path.stat()
        if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
            fail('UNSAFE_PATH', 'Unexpected filesystem object.', path=relative)
        return path

    def _read(self, relative, maximum=MAX_FILE_BYTES):
        path = self._checked(relative)
        fd = fs.open_file(path, os.O_RDONLY)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                fail('INVALID_DATA', 'File is not regular or exceeds the size limit.', path=relative)
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                raw = stream.read(maximum + 1)
            if len(raw) > maximum or _signature(before) != _signature(os.fstat(fd)):
                fail('SOURCE_CHANGED', 'Source changed while being read.', path=relative)
            return raw
        finally:
            os.close(fd)

    def _inventory(self):
        directory = self._checked('data/issues', directory=True)
        paths = ['data/project.json', 'data/relations.json']
        if (self.root / 'project.json').exists() or (self.root / 'project.json').is_symlink():
            paths.append('project.json')
        paths += ['data/issues/' + p.name for p in directory.iterdir() if FILE_RE.fullmatch(p.name)]
        inventory = {}
        for path in sorted(paths):
            signature = list(_signature(self._checked(path).stat()))
            if HASH_INVENTORY:
                raw = self._read(path)
                self._inventory_bytes_read += len(raw)
                # Keep parsed-record reuse, but never rely on Windows creation
                # time to detect same-size edits with restored modification time.
                signature[4] = int(digest(raw), 16)
            inventory[path] = signature
        return inventory

    @contextlib.contextmanager
    def _lock(self):
        rootfd = fs.open_dir(self.root)
        fd = dirfd = None
        try:
            # Concurrent initial creation can transiently return ENOENT on macOS.
            # Keep the same checked directory descriptor and never follow links.
            for attempt in range(3):
                try:
                    fd = fs.open_file('.research-desk.lock', os.O_RDWR | os.O_CREAT, parent=rootfd)
                    break
                except FileNotFoundError:
                    if attempt == 2:
                        raise
                    time.sleep(0.01)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                fail('UNSAFE_PATH', 'Index lock must be a regular file.')
            deadline = time.monotonic() + self.lock_timeout
            while True:
                try:
                    fs.try_lock(fd)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        fail('INDEX_BUSY', 'Another process holds the index lock; retry later.')
                    time.sleep(0.02)
            self._held_lock = fd
            self._assert_lock_current()
            directory = self.root / '.cache'
            directory.mkdir(exist_ok=True)
            self._checked('.cache', directory=True)
            dirfd = fs.open_dir(directory)
            yield dirfd
        finally:
            self._held_lock = None
            if fd is not None:
                os.close(fd)
            if dirfd is not None:
                fs.close_dir(dirfd)
            fs.close_dir(rootfd)

    def _assert_lock_current(self):
        path_stat = self._checked('.research-desk.lock').stat()
        held_stat = os.fstat(self._held_lock)
        if (path_stat.st_dev, path_stat.st_ino) != (held_stat.st_dev, held_stat.st_ino):
            fail('LOCK_REPLACED', 'Project lock was replaced; stop and retry without removing the lock file.')

    def _assert_readable(self):
        try:
            self._checked('data/transactions/pending.json')
        except FileNotFoundError:
            return
        fail('PENDING_TRANSACTION', 'An interrupted write needs recovery. Run recover status, then recover finish; ordinary reads do not mutate sources.')

    def _load_cache(self):
        try:
            raw = self._read('.cache/issues-index.json', MAX_CACHE_BYTES)
            cache = json_read(raw, '.cache/issues-index.json')
            if not isinstance(cache, dict):
                return None
            checksum = cache.pop('checksum', None)
            if cache.get('schema_version') != SCHEMA or cache.get('parser_fingerprint') != PARSER_FINGERPRINT or cache.get('root') != digest(str(self.root)) or digest(canonical(cache)) != checksum:
                return None
            if not all(k in cache for k in ('manifest', 'records', 'relations', 'raw_relations', 'project', 'generation', 'adjacency')):
                return None
            manifest, records = cache['manifest'], cache['records']
            if not isinstance(manifest, dict) or not isinstance(records, dict):
                return None
            if not {'data/project.json', 'data/relations.json'} <= set(manifest):
                return None
            paths = set(manifest) - {'data/project.json', 'data/relations.json', 'project.json'}
            if any(not p.startswith('data/issues/') or not FILE_RE.fullmatch(p[12:]) for p in paths):
                return None
            if set(records) != {Path(p).stem.upper() for p in paths}:
                return None
            for entry in manifest.values():
                if not isinstance(entry, dict) or set(entry) != {'stat', 'sha256'}:
                    return None
                if not isinstance(entry['stat'], list) or len(entry['stat']) != 5 or any(type(v) is not int for v in entry['stat']):
                    return None
                if not isinstance(entry['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', entry['sha256']):
                    return None
            for identifier, item in records.items():
                path = 'data/issues/' + identifier.lower() + '.md'
                if not isinstance(item, dict) or set(item) != FIELDS or item['id'] != identifier or item['path'] != path or item['source_hash'] != manifest[path]['sha256']:
                    return None
                if not _text(item['title'], 1000) or not isinstance(item['kind'], str) or item['kind'] not in KINDS or not isinstance(item['status'], str) or item['status'] not in STATUS_TYPES:
                    return None
                if type(item['priority']) is not int or not 0 <= item['priority'] <= 4 or type(item['archived']) is not bool:
                    return None
                if any(v is not None and not _id(v) for v in (item['parent'], item['duplicate_of'])):
                    return None
                if any(not isinstance(item[k], list) or len(item[k]) > 100 or any(not _text(v, 200) for v in item[k]) for k in ('labels', 'tags')):
                    return None
                if not isinstance(item['excerpt'], str) or len(item['excerpt']) > 2000 or item['excerpt_source'] not in (None, 'desk_summary', 'Statement and scope (verbatim block)') or not (item['origin'] == 'local' and item['source_url'] is None or _web_url(item['source_url'])) or not _timestamp(item['modified_at']):
                    return None
                if item['origin'] not in ('local', 'imported') or not isinstance(item['body_hash'], str) or not re.fullmatch('[0-9a-f]{64}', item['body_hash']):
                    return None
                if item['statement_role'] != _statement_role(item['kind'], item['claim_ref']) or not isinstance(item['proposals'], list):
                    return None
                validate_source_refs(item['source_refs'])
                validate_outcome(item['outcome'], item['kind'])
                if any(item[k] is not None and not _text(item[k], 2000) for k in ('integration_key', 'next_action', 'priority_rationale')):
                    return None
                if not isinstance(item['blocked_by'], list) or any(not _id(v) for v in item['blocked_by']):
                    return None
                if item['excerpt_scope_complete'] is not None and type(item['excerpt_scope_complete']) is not bool:
                    return None
                if not isinstance(item['source_warnings'], list) or any(w not in ('unterminated_code_fence', 'unterminated_display_math', 'ambiguous_statement_and_scope') for w in item['source_warnings']):
                    return None
            if not isinstance(cache['project'], dict) or not isinstance(cache['raw_relations'], list):
                return None
            return cache
        except FileNotFoundError:
            return None
        except IndexErrorDetail as e:
            if e.code == 'UNSAFE_PATH':
                raise
            return None

    def _save_cache(self, cache, dirfd):
        payload = dict(cache, checksum=digest(canonical(cache)))
        raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
        if len(raw) > MAX_CACHE_BYTES:
            fail('INDEX_TOO_LARGE', 'Cache exceeds the supported size; sources were not modified.')
        name = 'issues-index-' + os.urandom(12).hex() + '.tmp'
        fd = fs.open_file(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, parent=dirfd)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            fs.replace(name, 'issues-index.json', dirfd)
            fs.sync_dir(dirfd)
        finally:
            try:
                fs.unlink(name, dirfd)
            except FileNotFoundError:
                pass

    def refresh(self, force=False):
        """Stat all canonical sources; only reparse changed files unless force=True."""
        with self._lock() as dirfd:
            self._assert_readable()
            return self._refresh_locked(dirfd, force)

    def _refresh_locked(self, dirfd, force=False):
        cached = None if force else self._load_cache()
        for attempt in range(3):
            try:
                self._inventory_bytes_read = 0
                before = self._inventory()
                records, manifest, values = {}, {}, {}
                stats = {'scanned_issues': sum(p.startswith('data/issues/') for p in before), 'issue_files_read': 0, 'json_files_read': 0,
                         'source_bytes_read': 0, 'attempts': attempt + 1, 'cache_reused': False}
                for path, signature in before.items():
                    old = cached and cached['manifest'].get(path)
                    if old and old['stat'] == signature:
                        manifest[path] = old
                        if path.startswith('data/issues/'):
                            identifier = Path(path).stem.upper()
                            records[identifier] = cached['records'][identifier]
                        else:
                            values[path] = cached.get('registration') if path == 'project.json' else (cached['project'] if path == 'data/project.json' else cached['raw_relations'])
                        continue
                    raw = self._read(path)
                    stats['source_bytes_read'] += len(raw)
                    manifest[path] = {'stat': signature, 'sha256': digest(raw)}
                    if path.startswith('data/issues/'):
                        identifier = Path(path).stem.upper()
                        records[identifier] = record(raw, identifier, path)
                        stats['issue_files_read'] += 1
                    else:
                        values[path] = json_read(raw, path)
                        stats['json_files_read'] += 1
                project = values['data/project.json']
                if not isinstance(project, dict) or not _text(project.get('id')) or not _text(project.get('name')) or not (project.get('source_url') is None or _web_url(project.get('source_url'))):
                    fail('INVALID_DATA', 'Invalid project metadata.')
                if 'project.json' in values:
                    from ticket_project import validate_config, validate_paper_registration
                    validate_config(values['project.json'])
                    if 'subject' in values['project.json']:
                        validate_paper_registration(self.root, values['project.json'], project)
                edges, adjacency = relation_graph(records, values['data/relations.json'])
                if before != self._inventory():
                    cached = None
                    continue
                generation = digest(canonical({'parser': PARSER_FINGERPRINT,
                                               'sources': {p: m['sha256'] for p, m in manifest.items()}}))
                snapshot = {'schema_version': SCHEMA, 'parser_fingerprint': PARSER_FINGERPRINT,
                            'root': digest(str(self.root)), 'generation': generation,
                            'manifest': manifest, 'records': records, 'project': project,
                            'raw_relations': values['data/relations.json'], 'relations': edges,
                            'adjacency': adjacency, 'registration': values.get('project.json')}
                if cached and snapshot == cached:
                    stats['cache_reused'] = True
                else:
                    self._save_cache(snapshot, dirfd)
                stats["inventory_bytes_read"] = self._inventory_bytes_read
                self.last_stats = stats
                return snapshot
            except IndexErrorDetail as e:
                if e.code != 'SOURCE_CHANGED':
                    raise
                cached = None
            except FileNotFoundError:
                cached = None
        fail('SOURCE_CHANGED', 'Sources were unavailable or changed repeatedly while indexing; no query result was served.')

    def validate(self):
        snapshot = self.refresh(force=True)
        return {'ok': True, 'generation': snapshot['generation'], 'issues': len(snapshot['records']),
                'relations': len(snapshot['relations']), 'verification': 'full source hashes and schema/references',
                'stats': self.last_stats}

    def list_issues(self, *, kind=None, status=None, priority=None, parent=None, tag=None, outcome=None,
                    include_archived=False, include_duplicates=False, limit=10, cursor=None,
                    fields=DEFAULT_FIELDS, query=None):
        if kind is not None and (not isinstance(kind, str) or kind not in KINDS) or status is not None and (not isinstance(status, str) or status not in STATUS_TYPES):
            fail('INVALID_ARGUMENT', 'Unknown issue kind or status.')
        if priority is not None and (type(priority) is not int or not 0 <= priority <= 4):
            fail('INVALID_ARGUMENT', 'priority must be between 0 and 4.')
        if outcome is not None and (not isinstance(outcome, str) or outcome not in OUTCOMES):
            fail('INVALID_ARGUMENT', 'Unknown empirical outcome.')
        if parent is not None and not _id(parent):
            fail('INVALID_ARGUMENT', 'Invalid parent ID.')
        if not isinstance(fields, (list, tuple)) or not fields or any(not isinstance(f, str) or f not in FIELDS for f in fields) or len(set(fields)) != len(fields):
            fail('INVALID_ARGUMENT', 'Unknown or repeated output field.')
        tags = normalize_tags(tag)
        if type(include_archived) is not bool or type(include_duplicates) is not bool:
            fail('INVALID_ARGUMENT', 'Invalid tag or inclusion flag.')
        if query is not None and (not isinstance(query, str) or not query.strip() or len(query) > 256):
            fail('INVALID_ARGUMENT', 'Search text must contain 1–256 characters.')
        snapshot = self.refresh()
        terms = unicodedata.normalize('NFKC', query).casefold().split() if query else []
        found = []
        for item in snapshot['records'].values():
            if item['archived'] and not include_archived or item['status'] == 'Duplicate' and not include_duplicates:
                continue
            if any(v is not None and item[k] != v for k, v in (('kind', kind), ('status', status), ('priority', priority), ('parent', parent), ('outcome', outcome))):
                continue
            if not set(tags) <= set(item['tags'] + item['labels']):
                continue
            haystack = unicodedata.normalize('NFKC', ' '.join([item['id'], item['title'], item['excerpt'], item['outcome'] or ''] + item['tags'] + item['labels'])).casefold()
            if not all(term in haystack for term in terms):
                continue
            found.append(item)
        found.sort(key=lambda i: (i['priority'] or 5, int(i['id'][4:])))
        args = dict(command='search' if query else 'list', kind=kind, status=status, priority=priority,
                    parent=parent, tag=tags, include_archived=include_archived, include_duplicates=include_duplicates,
                    fields=list(fields), query=query, outcome=outcome)
        result = _page([{k: item[k] for k in fields} for item in found], snapshot, args, limit, cursor)
        if query:
            result['search_scope'] = 'id,title,tags,labels,outcome,explicit summary or short verbatim scope block; not full text or source contents'
        return result

    def search(self, query, **options):
        return self.list_issues(query=query, **options)

    def neighbors(self, identifier, *, relation_type=None, direction='both', group=None,
                  include_noncurrent=False, limit=10, cursor=None):
        if not _id(identifier) or direction not in ('incoming', 'outgoing', 'both') or relation_type is not None and (not isinstance(relation_type, str) or relation_type not in RELATION_TYPES) or type(include_noncurrent) is not bool:
            fail('INVALID_ARGUMENT', 'Invalid ID, direction or relation type.')
        group = group or ('administrative' if relation_type == 'contains' else 'research')
        if group not in ('administrative', 'research', 'all'):
            fail('INVALID_ARGUMENT', 'Unknown relation group.')
        snapshot = self.refresh()
        if identifier not in snapshot['records']:
            fail('NOT_FOUND', 'Unknown issue.', id=identifier)
        adjacency = snapshot['adjacency'][identifier]
        keys = set(adjacency['incoming'] if direction == 'incoming' else adjacency['outgoing'] if direction == 'outgoing' else adjacency['incoming'] + adjacency['outgoing'])
        edges = [copy.deepcopy(e) for e in snapshot['relations'] if e['key'] in keys
                 and (not relation_type or e['type'] == relation_type)
                 and (group == 'all' or e['group'] == group)
                 and (include_noncurrent or e['status'] == 'current')]
        args = dict(command='neighbors', id=identifier, relation_type=relation_type, direction=direction,
                    group=group, include_noncurrent=include_noncurrent)
        return _page(edges, snapshot, args, limit, cursor)

    def get_section(self, identifier, *, section=None, notes=False, max_chars=3000, cursor=None):
        if not _id(identifier) or section is not None and (notes or not isinstance(section, str) or len(section) > 4096) or type(notes) is not bool or type(max_chars) is not int or not 1 <= max_chars <= MAX_SECTION_CHARS:
            fail('INVALID_ARGUMENT', 'Invalid ID, section selection or max_chars (1–100000).')
        for _ in range(3):
            snapshot = self.refresh()
            item = snapshot['records'].get(identifier)
            if not item:
                fail('NOT_FOUND', 'Unknown issue.', id=identifier)
            try:
                raw = self._read(item['path'])
            except FileNotFoundError:
                continue
            except IndexErrorDetail as e:
                if e.code != 'SOURCE_CHANGED':
                    raise
                continue
            if digest(raw) == item['source_hash']:
                break
        else:
            fail('SOURCE_CHANGED', 'Issue changed during retrieval.')
        _, body, local_notes = parse_note(raw.decode('utf-8'), identifier)
        warnings = []
        available = sections(body, warnings)
        text = local_notes if notes else body
        if section is not None:
            matches = [s for s in available if s['name'].casefold() == section.casefold()]
            if len(matches) != 1:
                fail('AMBIGUOUS_SECTION' if matches else 'NOT_FOUND', 'Section must match one heading.', section=section,
                     path=item['path'], available=[s['name'][:200] for s in available[:20]],
                     available_truncated=len(available) > 20 or any(len(s['name']) > 200 for s in available[:20]),
                     source_warnings=warnings, section_scan_complete=not warnings)
            text = body[matches[0]['start']:matches[0]['end']]
        args = dict(command='show', id=identifier, section=section, notes=notes)
        generation = digest(item['source_hash'] + PARSER_FINGERPRINT)
        offset = _cursor_offset(cursor, generation, args)
        spans = blocks(text, warnings)
        warnings = sorted(set(warnings))
        if offset not in {0, len(text)} | {a for a, _ in spans}:
            fail('INVALID_CURSOR', 'Cursor is not at a block boundary.')
        end = offset
        for start, stop in spans:
            if start < offset:
                continue
            if stop - offset > max_chars:
                if end == offset:
                    fail('BLOCK_TOO_LARGE', 'Increase max_chars to read this complete paragraph, table or math block.',
                         path=item['path'], source_warnings=warnings, required_chars=stop - start, maximum=MAX_SECTION_CHARS)
                break
            end = stop
        return {'ok': True, 'id': identifier, 'path': item['path'], 'source_hash': item['source_hash'],
                'section': section, 'notes': notes, 'content': text[offset:end],
                'source_warnings': warnings,
                'range': {'start': offset, 'end': end, 'unit': 'unicode-codepoints'},
                'truncated': end < len(text),
                'next_cursor': _cursor_encode(generation, args, end) if end < len(text) else None}
