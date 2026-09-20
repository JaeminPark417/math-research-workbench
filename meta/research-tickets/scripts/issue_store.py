"""Canonical local issue writes and explicit research-session workflow.

All callers, including the Node HTTP adapter, share the project lock and journal.
Research selection is operational; this module verifies neither proofs nor empirical claims.
"""
import copy
from pathlib import Path
import re
import uuid

import issue_index as ix
import issue_transaction as tx

FIELDS = {'title': 'desk_title', 'status': 'desk_status', 'priority': 'desk_priority',
          'parent': 'desk_parent', 'labels': 'desk_labels', 'tags': 'desk_tags',
          'archived': 'desk_archived', 'summary': 'desk_summary',
          'blocked_by': 'desk_blocked_by', 'next_action': 'desk_next_action',
          'priority_rationale': 'desk_priority_rationale', 'claim_ref': 'desk_claim_ref',
          'source_refs': 'desk_source_refs', 'outcome': 'desk_outcome'}
MAX_RUN_BYTES = 2 * 1024 * 1024
END_RESERVE_BYTES = 256 * 1024


def require(value, message, code='INVALID_ARGUMENT', **details):
    if not value:
        ix.fail(code, message, **details)


def text(value, maximum=2000):
    require(ix._text(value, maximum), 'Expected nonempty text within the supported length.')
    return value


def verified_source_refs(root, value):
    from issue_sources import verify_reference
    try:
        return [verify_reference(root, ref) for ref in ix.validate_source_refs(value)]
    except ix.IndexErrorDetail as error:
        if error.code == 'INVALID_DATA':
            ix.fail('INVALID_ARGUMENT', str(error), **error.details)
        raise


def render(raw, changes, body=None, notes=None):
    """Keep untouched frontmatter/body bytes, including Windows line endings."""
    eol = '\r\n' if raw.startswith('---\r\n') else '\n'
    boundary = eol + '---' + eol
    end = raw.index(boundary, 3 + len(eol))
    lines = raw[3 + len(eol):end].split(eol)
    present = set()
    out = []
    for line in lines:
        name = line.split(':', 1)[0]
        present.add(name)
        out.append(name + ': ' + ix.canonical(changes[name]) if name in changes else line)
    out.extend(name + ': ' + ix.canonical(value) for name, value in changes.items() if name not in present)
    marker = ix.MARKER.replace('\n', eol)
    old_body, old_notes = raw[end + len(boundary):].split(marker)
    def updated(value):
        return value.replace('\r\n', '\n').replace('\n', eol)
    return ('---' + eol + eol.join(out) + boundary
            + (old_body if body is None else updated(body)) + marker
            + (old_notes if notes is None else updated(notes)))


def web_issue(raw, identifier):
    meta, body, notes = ix.parse_note(raw, identifier)
    return {'id': identifier, 'title': meta['desk_title'], 'kind': meta['desk_kind'],
            'labels': meta['desk_labels'], 'status': meta['desk_status'], 'statusType': meta['desk_status_type'],
            'priority': meta['desk_priority'], 'parent': meta['desk_parent'], 'duplicateOf': meta['desk_duplicate_of'],
            'archived': meta['desk_archived'], 'sourceUrl': meta['desk_source_url'],
            'importedAt': meta.get('desk_imported_at'), 'originUpdatedAt': meta.get('desk_origin_updated_at'),
            'modifiedAt': meta['desk_modified_at'], 'body': body, 'notes': notes,
            'version': ix.digest(raw), 'file': 'data/issues/' + identifier.lower() + '.md',
            'sourceRefs': meta.get('desk_source_refs', []), 'outcome': meta.get('desk_outcome')}


class IssueStore:
    def __init__(self, root, lock_timeout=3):
        self.index = ix.IssueIndex(root, lock_timeout)

    def _harness(self):
        raw = tx.optional(self.index, 'data/harness.json')
        value = ix.json_read(raw, 'data/harness.json') if raw is not None else {'schema': 1, 'active': None, 'last_run': None}
        require(isinstance(value, dict) and value.get('schema') == 1 and set(value) == {'schema', 'active', 'last_run'}, 'Invalid harness state.', 'INVALID_DATA')
        for field in ('active', 'last_run'):
            if value[field] is not None:
                tx.key(value[field])
        return value, raw

    def _run(self, identifier):
        path = 'data/runs/' + tx.key(identifier) + '.json'
        raw = tx.optional(self.index, path)
        require(raw is not None, 'Research run does not exist.', 'NOT_FOUND', run_id=identifier)
        value = ix.json_read(raw, path)
        require(isinstance(value, dict) and value.get('schema') == 1 and value.get('id') == identifier and ix._id(value.get('issue')) and value.get('status') in ('active', 'completed', 'paused', 'blocked') and isinstance(value.get('events'), list), 'Invalid research run.', 'INVALID_DATA')
        require(ix._timestamp(value.get('started_at')) and ix._text(value.get('selection_reason'), 2000) and ix._text(value.get('next_action'), 2000) and 1 <= len(value['events']) <= 1000, 'Invalid run metadata/events.', 'INVALID_DATA')
        require(value['status'] == 'active' or ix._timestamp(value.get('ended_at')), 'Closed run needs an end time.', 'INVALID_DATA')
        if 'math_run' in value:
            ref = value['math_run']
            require(isinstance(ref, dict) and set(ref) == {'run_id', 'source', 'object_ids'} and ix._text(ref['run_id'], 200) and isinstance(ref['object_ids'], list) and len(ref['object_ids']) <= 100 and all(ix._text(v, 200) for v in ref['object_ids']), 'Invalid persistent math-run binding.', 'INVALID_DATA')
            from issue_sources import validate_reference
            validate_reference(ref['source'])
        for event in value['events']:
            require(isinstance(event, dict) and event.get('phase') in ('begin', 'checkpoint', 'end') and ix._timestamp(event.get('at')) and ix._text(event.get('summary'), 2000) and ix._text(event.get('next_action'), 2000) and isinstance(event.get('evidence'), list) and isinstance(event.get('created'), dict), 'Invalid run event.', 'INVALID_DATA')
        return value, raw

    def _validate_harness(self, records, state=None, run=None):
        state = state if state is not None else self._harness()[0]
        if state['active']:
            run = run if run is not None else self._run(state['active'])[0]
            issue = records.get(run['issue'])
            require(run['id'] == state['active'] and run['status'] == 'active' and issue is not None and issue['kind'] == 'activity' and issue['status'] in ('In Progress', 'In Review') and not issue['archived'], 'Active run and activity disagree; end the run before archiving/changing its status.', 'WORKFLOW_CONFLICT')
        if state['last_run']:
            last = run if run is not None and run['id'] == state['last_run'] else self._run(state['last_run'])[0]
            require(last['status'] in ('completed', 'paused', 'blocked') and last['issue'] in records and records[last['issue']]['kind'] == 'activity', 'Last run must reference a closed activity run.', 'WORKFLOW_CONFLICT')

    def read_web(self, identifier=None):
        with self.index._lock() as fd:
            self.index._assert_readable()
            snapshot = self.index._refresh_locked(fd)
            self._validate_harness(snapshot['records'])
            if identifier is not None:
                require(ix._id(identifier), 'Invalid issue ID.')
                require(identifier in snapshot['records'], 'Issue not found.', 'NOT_FOUND')
                return web_issue(self.index._read(snapshot['records'][identifier]['path']).decode('utf-8'), identifier)
            issues = [web_issue(self.index._read(item['path']).decode('utf-8'), identifier)
                      for identifier, item in sorted(snapshot['records'].items(), key=lambda pair: int(pair[0][4:]))]
            return {'project': snapshot['project'], 'issues': issues,
                    'relations': [{k: v for k, v in edge.items() if k != 'group'} for edge in snapshot['relations']],
                    'revision': snapshot['generation']}

    def workflow_start(self, limit=5, cursor=None, tag=None):
        tags = ix.normalize_tags(tag)
        with self.index._lock() as fd:
            self.index._assert_readable()
            snapshot = self.index._refresh_locked(fd)
            state, raw = self._harness()
            self._validate_harness(snapshot['records'], state)
            active = None
            if state['active']:
                run, run_raw = self._run(state['active'])
                active = {k: run.get(k) for k in ('id', 'issue', 'started_at', 'status', 'next_action')}
                active['version'] = ix.digest(run_raw)
                item = snapshot['records'][active['issue']]
                active.update(tags=item['tags'], labels=item['labels'], matches_filter=set(tags) <= set(item['tags'] + item['labels']))
            items = []
            for item in snapshot['records'].values():
                if item['kind'] != 'activity' or item['status'] not in ('Ready', 'Todo') or item['archived']:
                    continue
                if any(snapshot['records'][blocker]['status'] != 'Done' for blocker in item['blocked_by']):
                    continue
                if not set(tags) <= set(item['tags'] + item['labels']):
                    continue
                items.append({k: item[k] for k in ('id', 'title', 'priority', 'source_hash', 'next_action', 'priority_rationale', 'tags', 'labels')})
            items.sort(key=lambda item: (item['priority'] or 5, int(item['id'][4:])))
            result = ix._page(items, snapshot, {'command': 'workflow-start', 'harness_version': ix.digest(raw or ''), 'tag': tags}, limit, cursor)
            result.update(harness_version=ix.digest(raw or ''), active=active,
                          requested_tags=tags,
                          untracked_in_progress=[i['id'] for i in snapshot['records'].values() if i['kind'] == 'activity' and i['status'] in ('In Progress', 'In Review') and not i['archived'] and (not active or i['id'] != active['issue'])][:20],
                          selection_rule='Priority order among operationally ready activities; research relations and results never imply readiness. Agent rule: conditional follow-ups remain Backlog until an explicit recorded decision activates them; the writer does not enforce that decision gate.')
            result['coverage'] = (snapshot.get('registration') or {}).get('coverage', {'state': 'partial', 'scope': 'Legacy test fixture', 'untracked': ['Consult the project capsule and research ledger.']})
            subject = (snapshot.get('registration') or {}).get('subject')
            result['capsule'] = '../../' + subject['note'] if subject else '../README.md'
            result['subject'] = subject
            identifiers = [v['id'] for v in result['items']] + ([active['issue']] if active else [])
            checks = self._source_check_page(snapshot, identifiers, limit=20)
            result.update(source_checks=checks['checks'], source_check_ids=checks['ids'],
                          source_checks_truncated=checks['truncated'],
                          source_checks_next_cursor=checks['next_cursor'],
                          source_checks_total=checks['total'])
            if active:
                active['math_run'] = run.get('math_run')
            result['last_run'] = None
            if state['last_run']:
                last, last_raw = self._run(state['last_run'])
                result['last_run'] = {k: last.get(k) for k in ('id', 'issue', 'status', 'ended_at', 'next_action', 'math_run')}
                result['last_run']['version'] = ix.digest(last_raw)
                item = snapshot['records'][last['issue']]
                result['last_run'].update(tags=item['tags'], labels=item['labels'], matches_filter=set(tags) <= set(item['tags'] + item['labels']))
            return result

    def _source_check_page(self, snapshot, identifiers, limit=20, cursor=None):
        from issue_sources import check_drift
        require(isinstance(identifiers, list) and len(identifiers) <= 51 and
                all(ix._id(v) for v in identifiers), 'Supply at most 51 valid issue IDs.')
        identifiers = sorted(set(identifiers), key=lambda value: int(value[4:]))
        require(all(v in snapshot['records'] for v in identifiers), 'Issue not found.', 'NOT_FOUND')
        checked, references = set(), []
        for identifier in identifiers:
            while identifier and identifier not in checked:
                checked.add(identifier)
                item = snapshot['records'][identifier]
                if item['claim_ref']:
                    references.append({'issue': identifier, 'source': item['claim_ref']})
                for number, ref in enumerate(item.get('source_refs', [])):
                    references.append({'issue': identifier, 'source_field': 'source_refs',
                                       'source_index': number, 'source': ref})
                identifier = item['parent']
        page = ix._page(references, snapshot, {'command': 'source-check', 'ids': identifiers}, limit, cursor)
        page['ids'] = identifiers
        page['checks'] = [{**{k: v for k, v in ref.items() if k != 'source'},
                           **{k: v for k, v in ref['source'].items() if k != 'sha256'},
                           'reference_sha256': ref['source']['sha256'],
                           **check_drift(self.index.root, ref['source'])} for ref in page.pop('items')]
        return page

    def source_check(self, identifiers, limit=20, cursor=None):
        with self.index._lock() as fd:
            self.index._assert_readable()
            return self._source_check_page(self.index._refresh_locked(fd), identifiers, limit, cursor)

    def workflow_run(self, run_id, limit=5, cursor=None):
        with self.index._lock():
            self.index._assert_readable()
            run, raw = self._run(run_id)
            result = ix._page(run['events'], {'generation': ix.digest(raw)}, {'command': 'workflow-run', 'run_id': run_id}, limit, cursor)
            result['run'] = {k: v for k, v in run.items() if k != 'events'}
            return result

    def recover(self, mode='status', expected_journal=None, expected_files=None):
        with self.index._lock() as fd:
            if mode == 'status':
                return tx.status(self.index)
            if mode == 'finish':
                require(isinstance(expected_journal, str), 'Inspect recovery status and supply expected_journal.')
                result = tx.finish(self.index, expected_journal)
            elif mode == 'keep-current':
                require(isinstance(expected_journal, str) and isinstance(expected_files, dict),
                        'Inspect recovery status and supply expected_journal and expected_files.')
                def validate():
                    self._validate_harness(self.index._refresh_locked(fd, force=True)['records'])
                result = tx.keep_current(self.index, expected_journal, expected_files, validate)
            else:
                ix.fail('INVALID_ARGUMENT', 'Unknown recovery mode.')
            try:
                result['generation'] = self.index._refresh_locked(fd)['generation']
                result['index_updated'] = True
            except (OSError, ix.IndexErrorDetail) as error:
                result['index_updated'] = False
                result['index_error'] = getattr(error, 'code', 'FILESYSTEM_ERROR')
            return result

    def apply(self, request):
        require(isinstance(request, dict) and set(request) <= {'operation_id', 'expected_generation', 'expected_harness_version', 'expected_run_version', 'operations'}, 'Invalid write request keys.')
        operation_id = tx.key(request.get('operation_id'))
        try:
            request_hash = ix.digest(ix.canonical(request))
        except (TypeError, ValueError, UnicodeError, RecursionError):
            ix.fail('INVALID_ARGUMENT', 'Request must contain finite UTF-8 JSON values.')
        with self.index._lock() as fd:
            tx.finish(self.index)  # Only write entry points recover automatically.
            previous = tx.receipt(self.index, operation_id)
            if previous:
                require(previous['request_hash'] == request_hash, 'Operation ID was already used with another request.', 'OPERATION_REUSED')
                require(previous['status'] == 'applied', 'Operation was explicitly abandoned; use a new operation ID.', 'OPERATION_ABANDONED')
                return dict(previous['result'], replayed=True)
            snapshot = self.index._refresh_locked(fd)
            require(request.get('expected_generation') == snapshot['generation'], 'Index generation changed. Refresh and review before writing.', 'CONFLICT')
            return self._apply_locked(fd, snapshot, request, request_hash)

    def patch_web(self, identifier, payload):
        require(ix._id(identifier), 'Invalid issue ID.')
        require(isinstance(payload, dict) and set(payload) <= {'version', 'status', 'priority', 'notes'}, 'Unsupported web patch field.')
        require(isinstance(payload.get('version'), str), 'Read the current issue version before saving.', 'CONFLICT')
        with self.index._lock() as fd:
            tx.finish(self.index)
            snapshot = self.index._refresh_locked(fd)
            require(identifier in snapshot['records'], 'Issue not found.', 'NOT_FOUND')
            current = snapshot['records'][identifier]
            require(current['source_hash'] == payload['version'], 'Issue changed; preserve the draft and compare the current file.', 'CONFLICT')
            if 'status' in payload:
                require((payload['status'] != 'Duplicate' or current['status'] == 'Duplicate') and (current['status'] != 'Duplicate' or payload['status'] == 'Duplicate'), 'Duplicate history is preserved.')
            changes = {k: v for k, v in payload.items() if k != 'version'}
            if 'priority' in changes and changes['priority'] != current['priority']:
                changes['priority_rationale'] = 'Priority explicitly changed through the local web interface.'
            request = {'operation_id': 'web-' + uuid.uuid4().hex, 'expected_generation': snapshot['generation'],
                       'operations': [{'op': 'update', 'id': identifier, 'expected_version': payload['version'], 'changes': changes}]}
            self._apply_locked(fd, snapshot, request, ix.digest(ix.canonical(request)))
            return web_issue(self.index._read(current['path']).decode('utf-8'), identifier)

    def _apply_locked(self, fd, snapshot, request, request_hash):
        operations = request.get('operations')
        require(isinstance(operations, list) and 1 <= len(operations) <= 20 and all(isinstance(op, dict) for op in operations), 'A request needs 1–20 operations.')
        operation_id = request['operation_id']
        raws = {identifier: self.index._read(item['path']).decode('utf-8') for identifier, item in snapshot['records'].items()}
        require(all(ix.digest(raw) == snapshot['records'][identifier]['source_hash'] for identifier, raw in raws.items()), 'Sources changed before planning the write.', 'CONFLICT')
        old_raws = dict(raws)
        records = {identifier: ix.record(raw.encode('utf-8'), identifier, snapshot['records'][identifier]['path']) for identifier, raw in raws.items()}
        initial_records = copy.deepcopy(records)
        old_relations = self.index._read('data/relations.json').decode('utf-8')
        require(ix.digest(old_relations) == snapshot['manifest']['data/relations.json']['sha256'], 'Relations changed.', 'CONFLICT')
        initial_relations = ix.json_read(old_relations, 'data/relations.json')
        relations = copy.deepcopy(initial_relations)
        cache_differs = records != snapshot['records'] or relations != snapshot['raw_relations']
        ix.relation_graph(records, relations)
        state, old_state = self._harness()
        self._validate_harness(records, state)
        files, created, deferred_relations = {}, {}, []
        existing_keys = {r['integration_key'] for r in records.values() if r['integration_key'] is not None}
        next_id = max((int(i[4:]) for i in records), default=0) + 1
        for op in operations:
            if op.get('op') == 'create':
                stable_key = tx.key(op.get('key'))
                require(stable_key not in existing_keys and stable_key not in created, 'Integration key already exists; inspect the existing issue.', 'DUPLICATE_KEY', key=stable_key)
                created[stable_key] = 'RES-' + str(next_id)
                next_id += 1
        def resolve(identifier):
            if isinstance(identifier, str) and identifier.startswith('@'):
                require(identifier[1:] in created, 'Unknown new-issue reference.')
                return created[identifier[1:]]
            require(identifier is None or ix._id(identifier), 'Invalid issue reference.')
            return identifier
        def refresh_record(identifier):
            records[identifier] = ix.record(raws[identifier].encode(), identifier, 'data/issues/' + identifier.lower() + '.md')
        def change(identifier, changes, expected=None, workflow=False):
            identifier = resolve(identifier)
            require(identifier in raws, 'Issue not found.', 'NOT_FOUND')
            require(isinstance(changes, dict) and bool(changes) and set(changes) <= set(FIELDS) | {'body', 'notes'}, 'Unsupported or empty issue update.')
            if not workflow:
                original = old_raws.get(identifier)
                require(original is not None and expected == ix.digest(original), 'Issue version changed or was not supplied.', 'CONFLICT')
            before_meta, _, _ = ix.parse_note(raws[identifier], identifier)
            if before_meta.get('desk_claim_ref'):
                require('body' not in changes, 'Bound bodies are preserved; use propose for mathematical formulations or create a new versioned research record.', 'PROMOTION_REQUIRED')
                if 'claim_ref' in changes:
                    identity = ('repository', 'path', 'heading', 'object_id')
                    require(isinstance(changes['claim_ref'], dict) and all(changes['claim_ref'].get(k) == before_meta['desk_claim_ref'].get(k) for k in identity), 'A binding cannot be removed or redirected to another source object; only its version may change.')
            metadata = {'desk_modified_at': tx.now()}
            if 'priority' in changes and changes['priority'] != before_meta['desk_priority']:
                text(changes.get('priority_rationale'))
            for field, value in changes.items():
                if field in ('body', 'notes'):
                    require(isinstance(value, str) and len(value) <= (100000 if field == 'body' else 50000) and ix.MARKER not in value, 'Body/notes exceeds its limit or contains the reserved marker.')
                    continue
                if field == 'parent':
                    value = resolve(value)
                if field == 'blocked_by':
                    require(isinstance(value, list), 'blocked_by must be an array.')
                    value = [resolve(v) for v in value]
                if field == 'claim_ref':
                    from issue_sources import verify_reference
                    value = verify_reference(self.index.root, value)
                if field == 'source_refs':
                    value = verified_source_refs(self.index.root, value)
                metadata[FIELDS[field]] = value
            if 'status' in changes:
                status = changes['status']
                require(isinstance(status, str) and status in ix.STATUS_TYPES, 'Unknown status.')
                require(status != 'Done' or before_meta['desk_kind'] == 'activity', 'Done is only activity completion, never proof verification or empirical support.')
                require(status != 'Duplicate' or before_meta['desk_status'] == 'Duplicate', 'Use a separately reviewed duplicate record; this writer does not invent duplicate targets.')
                require(before_meta['desk_status'] != 'Duplicate' or status == 'Duplicate', 'Existing duplicate history is preserved.')
                metadata['desk_status_type'] = ix.STATUS_TYPES[status]
            raws[identifier] = render(raws[identifier], metadata, changes.get('body'), changes.get('notes'))
            try:
                refresh_record(identifier)
            except ix.IndexErrorDetail as error:
                if error.code == 'INVALID_DATA':
                    ix.fail('INVALID_ARGUMENT', str(error), **error.details)
                raise
        workflow_ops = [op for op in operations if op.get('op') in ('begin', 'checkpoint', 'end')]
        require(len(workflow_ops) <= 1 and (not workflow_ops or operations[-1] is workflow_ops[0]), 'At most one workflow transition is allowed, and it must be last.')
        for op in operations:
            kind = op.get('op')
            if kind == 'create':
                require(set(op) <= {'op', 'key', 'title', 'kind', 'body', 'status', 'priority', 'parent', 'labels', 'tags', 'notes', 'summary', 'blocked_by', 'next_action', 'priority_rationale', 'claim_ref', 'source_refs', 'outcome'}, 'Unknown create field.')
                identifier = created[op['key']]
                issue_kind = op.get('kind')
                require(isinstance(issue_kind, str) and issue_kind in ix.KINDS, 'Unknown issue kind.')
                body = text(op.get('body'), 100000)
                notes = op.get('notes', '')
                require(isinstance(notes, str) and len(notes) <= 50000 and ix.MARKER not in body + notes, 'Invalid body or notes.')
                status = op.get('status', 'Backlog')
                require(status in ('Backlog', 'Ready', 'Todo'), 'New issues start in Backlog or Ready/Todo; completion needs a recorded activity.')
                stamp = tx.now()
                meta = {'desk_schema': 2, 'desk_id': identifier, 'desk_origin': 'local', 'desk_key': op['key'],
                        'desk_operation_id': operation_id, 'desk_title': text(op.get('title'), 1000), 'desk_kind': issue_kind,
                        'desk_status': status, 'desk_status_type': ix.STATUS_TYPES[status], 'desk_priority': op.get('priority', 3),
                        'desk_labels': op.get('labels', [issue_kind]), 'desk_tags': op.get('tags', []),
                        'desk_parent': resolve(op.get('parent')), 'desk_duplicate_of': None, 'desk_archived': False,
                        'desk_source_url': None, 'desk_created_at': stamp, 'desk_modified_at': stamp,
                        'desk_imported_at': None, 'desk_origin_updated_at': None}
                for field in ('summary', 'blocked_by', 'next_action', 'priority_rationale'):
                    if field in op:
                        meta[FIELDS[field]] = [resolve(v) for v in op[field]] if field == 'blocked_by' and isinstance(op[field], list) else op[field]
                if 'claim_ref' in op:
                    from issue_sources import verify_reference
                    meta['desk_claim_ref'] = verify_reference(self.index.root, op['claim_ref'])
                if 'source_refs' in op:
                    meta['desk_source_refs'] = verified_source_refs(self.index.root, op['source_refs'])
                if 'outcome' in op:
                    meta['desk_outcome'] = op['outcome']
                raws[identifier] = '---\n' + '\n'.join(k + ': ' + ix.canonical(v) for k, v in meta.items()) + '\n---\n' + body + ix.MARKER + notes
                try:
                    refresh_record(identifier)
                except ix.IndexErrorDetail as error:
                    if error.code == 'INVALID_DATA':
                        ix.fail('INVALID_ARGUMENT', str(error), **error.details)
                    raise
            elif kind in ('update', 'archive'):
                require(set(op) <= ({'op', 'id', 'expected_version', 'changes'} if kind == 'update' else {'op', 'id', 'expected_version', 'archived'}), 'Unknown update field.')
                changes = op.get('changes') if kind == 'update' else {'archived': op.get('archived', True)}
                change(op.get('id'), changes, op.get('expected_version'))
            elif kind == 'propose':
                require(set(op) <= {'op', 'id', 'expected_version', 'statement', 'reason'}, 'Unknown proposal field.')
                identifier = resolve(op.get('id'))
                require(identifier in old_raws and op.get('expected_version') == ix.digest(old_raws[identifier]), 'Read the current issue before proposing a change.', 'CONFLICT')
                require(records[identifier]['kind'] in {'theorem', 'lemma', 'obligation', 'counterexample', 'obstruction'}, 'propose is reserved for mathematical formulations; create a revised research record for experimental work.')
                meta, _, _ = ix.parse_note(raws[identifier], identifier)
                proposals = meta.get('desk_proposals', [])
                require(len(proposals) < 100 and not any(p['key'] == operation_id for p in proposals), 'Use a distinct operation for each proposed formulation; retain prior proposals.')
                proposals.append({'key': operation_id, 'status': 'proposed', 'statement': text(op.get('statement'), 100000), 'reason': text(op.get('reason')), 'at': tx.now(), 'base_ref': meta.get('desk_claim_ref')})
                raws[identifier] = render(raws[identifier], {'desk_proposals': proposals, 'desk_modified_at': tx.now()})
                refresh_record(identifier)
            elif kind in ('relation-add', 'relation-supersede'):
                deferred_relations.append(op)
            elif kind not in ('begin', 'checkpoint', 'end'):
                ix.fail('INVALID_ARGUMENT', 'Unknown operation.')
        # Changed claims, evidence or interpretation cannot silently reuse old edges.
        changed_bodies = {i for i in old_raws if any(records[i][field] != initial_records[i][field]
                          for field in ('body_hash', 'claim_ref', 'source_refs', 'outcome'))}
        for relation in relations:
            if relation['status'] == 'current' and (relation['from'] in changed_bodies or relation['to'] in changed_bodies):
                relation['status'] = 'needs-review'
                relation['stale_reason'] = 'Issue body, evidence source or outcome changed; previous endpoint versions are retained.'
        for op in deferred_relations:
            if op['op'] == 'relation-supersede':
                require(set(op) <= {'op', 'key', 'reason', 'replacement'}, 'Unknown supersede field.')
                target = next((r for r in relations if r['key'] == op.get('key')), None)
                require(target is not None, 'Relation not found.', 'NOT_FOUND')
                require(target['status'] in ('current', 'needs-review'), 'Relation already retired.')
                target['status'] = 'superseded'
                target['superseded_reason'] = text(op.get('reason'))
                if op.get('replacement') is not None:
                    target['superseded_by'] = tx.key(op['replacement'])
            else:
                require(set(op) <= {'op', 'key', 'from', 'to', 'type', 'route', 'logic', 'evidence', 'from_inline_target', 'to_inline_target'}, 'Unknown relation field.')
                relation = {k: copy.deepcopy(v) for k, v in op.items() if k != 'op'}
                relation['key'] = tx.key(op.get('key'))
                require(not relation['key'].startswith('contains-') and relation['key'] not in {r['key'] for r in relations}, 'Relation key is reserved or already exists.')
                require(isinstance(op.get('type'), str) and op['type'] in ix.RELATION_TYPES - {'contains'}, 'Invalid research relation type.')
                for field in ('route', 'logic', 'evidence'):
                    text(op.get(field))
                for side in ('from', 'to'):
                    identifier = resolve(op.get(side))
                    require(identifier in records, 'Relation endpoint not found.', 'DANGLING_REFERENCE')
                    relation[side] = identifier
                    relation[side + '_version'] = {'origin': 'local', 'path': records[identifier]['path'],
                        'heading': 'Issue body', 'sha256': records[identifier]['body_hash'], 'file_sha256': records[identifier]['source_hash']}
                    if records[identifier]['claim_ref']:
                        relation[side + '_version']['claim_ref'] = copy.deepcopy(records[identifier]['claim_ref'])
                    if records[identifier]['source_refs']:
                        relation[side + '_version']['source_refs'] = copy.deepcopy(records[identifier]['source_refs'])
                    if records[identifier]['outcome'] is not None:
                        relation[side + '_version']['outcome'] = records[identifier]['outcome']
                if relation['from'] == relation['to'] and relation['type'] == 'refutes':
                    text(relation.get('to_inline_target'))
                relation['status'] = 'current'
                relations.append(relation)
        for relation in relations:
            if relation.get('superseded_by'):
                require(relation['superseded_by'] != relation['key'] and relation['superseded_by'] in {r['key'] for r in relations}, 'Replacement relation is missing.', 'DANGLING_REFERENCE')
        ix.relation_graph(records, relations)
        run_result = None
        if workflow_ops:
            op = workflow_ops[0]
            run_result = self._transition(op, request, state, old_state, records, raws, created, files, change)
        else:
            self._validate_harness(records, state)
        # Capture the version actually published, including the final workflow edit.
        added_keys = {op['key'] for op in deferred_relations if op['op'] == 'relation-add'}
        for relation in relations:
            if relation['key'] in added_keys:
                for side in ('from', 'to'):
                    relation[side + '_version']['file_sha256'] = records[relation[side]]['source_hash']
        ix.relation_graph(records, relations)
        for identifier, raw in raws.items():
            old = old_raws.get(identifier)
            if old != raw:
                files[records[identifier]['path']] = (old, raw)
        if relations != initial_relations:
            files['data/relations.json'] = (old_relations, tx.encoded(relations))
        require(files, 'The request makes no changes.')
        require(self.index._inventory() == {p: item['stat'] for p, item in snapshot['manifest'].items()}, 'Source inventory changed before publication.', 'CONFLICT')
        hashes = {p: item['sha256'] for p, item in snapshot['manifest'].items()}
        for path, (_, after) in files.items():
            if path.startswith('data/issues/') or path == 'data/relations.json':
                hashes[path] = ix.digest(after)
        generation = ix.digest(ix.canonical({'parser': ix.PARSER_FINGERPRINT, 'sources': hashes}))
        result = {'ok': True, 'operation_id': operation_id, 'generation': generation, 'created': created,
                  'changed': sorted(files), 'run': run_result, 'replayed': False}
        tx.commit(self.index, operation_id, request_hash, files, result)
        try:
            result['generation'] = self.index._refresh_locked(fd, force=cache_differs)['generation']
            result['index_updated'] = True
        except (OSError, ix.IndexErrorDetail) as error:
            result['index_updated'] = False
            result['index_error'] = getattr(error, 'code', 'FILESYSTEM_ERROR')
        return result

    def _evidence(self, entries, raws, created):
        require(isinstance(entries, list) and len(entries) <= 20, 'Evidence must be an array of at most 20 references.')
        result = []
        for entry in entries:
            if isinstance(entry, dict) and 'source' in entry:
                require(set(entry) <= {'source', 'description'}, 'Invalid repository evidence reference.')
                from issue_sources import verify_reference
                result.append({'source': verify_reference(self.index.root, entry['source']), 'description': text(entry.get('description', 'Recorded source snapshot; no proof or remote-publication claim.'))})
                continue
            require(isinstance(entry, dict) and set(entry) <= {'issue', 'path', 'sha256', 'description'}, 'Invalid evidence reference.')
            require(('issue' in entry) != ('path' in entry), 'Evidence needs exactly one issue or path.')
            if 'issue' in entry:
                identifier = entry['issue']
                if isinstance(identifier, str) and identifier.startswith('@'):
                    identifier = created.get(identifier[1:])
                require(isinstance(identifier, str) and identifier in raws, 'Evidence issue does not exist.')
                path, raw = 'data/issues/' + identifier.lower() + '.md', raws[identifier]
                sha = ix.digest(raw)
                require('sha256' not in entry or entry['sha256'] == sha, 'Evidence issue changed since inspection.', 'CONFLICT', path=path)
            else:
                path = entry.get('path')
                require(isinstance(path, str) and not Path(path).is_absolute() and '..' not in Path(path).parts and
                        path.startswith(('artifacts/', 'notes/')) and Path(path).suffix in ('.md', '.txt', '.json', '.tex', '.lean', '.py', '.csv'), 'Use issue references, registered source references, or a local ticket artifact path.')
                raw = self.index._read(path)
                sha = ix.digest(raw)
                require(entry.get('sha256') == sha, 'Evidence changed since inspection.', 'CONFLICT', path=path)
            result.append({'path': path, 'sha256': sha, 'description': text(entry.get('description', 'Recorded local artifact.'))})
        return result

    def _transition(self, op, request, state, old_state, records, raws, created, files, change):
        phase = op['op']
        run_id = tx.key(op.get('run_id'))
        require(set(op) <= {'op', 'run_id', 'issue', 'reason', 'summary', 'next_action', 'evidence', 'outcome', 'math_run'}, 'Unknown workflow field.')
        require(phase == 'begin' or 'math_run' not in op, 'A session retains its original long-lived math run; start a new session to change it.')
        action = text(op.get('next_action'))
        summary = text(op.get('summary', op.get('reason')))
        run_path = 'data/runs/' + run_id + '.json'
        if phase == 'begin':
            require(request.get('expected_harness_version') == ix.digest(old_state or ''), 'Harness state changed.', 'CONFLICT')
            require(state['active'] is None, 'Another activity already owns the research run.', 'WIP_LIMIT')
            require(not any(r['kind'] == 'activity' and r['status'] in ('In Progress', 'In Review') and not r['archived'] for r in records.values()), 'Resolve the existing In Progress activity before starting another.', 'WIP_LIMIT')
            identifier = op.get('issue')
            if isinstance(identifier, str) and identifier.startswith('@'):
                identifier = created.get(identifier[1:])
            require(isinstance(identifier, str) and identifier in records and records[identifier]['kind'] == 'activity' and records[identifier]['status'] in ('Ready', 'Todo') and not records[identifier]['archived'], 'Select an operationally Ready activity.')
            require(all(records[i]['status'] == 'Done' for i in records[identifier]['blocked_by']), 'Activity has unfinished operational blockers.', 'BLOCKED')
            require(tx.optional(self.index, run_path) is None, 'Run ID already exists.', 'DUPLICATE_KEY')
            old_run = None
            run = {'schema': 1, 'id': run_id, 'issue': identifier, 'status': 'active', 'started_at': tx.now(),
                   'selection_reason': text(op.get('reason')), 'next_action': action, 'events': []}
            if op.get('math_run') is not None:
                ref = op['math_run']
                require(isinstance(ref, dict) and set(ref) == {'run_id', 'source', 'object_ids'} and isinstance(ref['object_ids'], list) and len(ref['object_ids']) <= 100, 'Math run needs run_id, source and bounded object_ids.')
                text(ref['run_id'], 200)
                for object_id in ref['object_ids']:
                    text(object_id, 200)
                from issue_sources import verify_reference
                run['math_run'] = dict(ref, source=verify_reference(self.index.root, ref['source']))
            state['active'] = run_id
            change(identifier, {'status': 'In Progress', 'next_action': action}, workflow=True)
        else:
            require(state['active'] == run_id, 'This run is not the active owner.', 'WORKFLOW_CONFLICT')
            run, old_run = self._run(run_id)
            require(request.get('expected_run_version') == ix.digest(old_run), 'Research run changed since inspection.', 'CONFLICT')
            require(run['status'] == 'active', 'The research run is not active.', 'WORKFLOW_CONFLICT')
            require(len(run['events']) < (1000 if phase == 'end' else 999), 'Run event limit reached; finish this run.')
            if phase == 'end':
                outcome = op.get('outcome')
                require(outcome in ('completed', 'paused', 'blocked'), 'Outcome must be completed, paused, or blocked.')
                require(outcome != 'completed' or bool(op.get('evidence')), 'Activity completion requires a recorded artifact.')
                run.update(status=outcome, ended_at=tx.now())
                state.update(active=None, last_run=run_id)
                change(run['issue'], {'status': {'completed': 'Done', 'paused': 'Ready', 'blocked': 'Backlog'}[outcome], 'next_action': action}, workflow=True)
            else:
                change(run['issue'], {'next_action': action}, workflow=True)
        evidence = self._evidence(op.get('evidence', []), raws, created)
        run['next_action'] = action
        run['events'].append({'at': tx.now(), 'phase': phase, 'operation_id': request['operation_id'],
                              'summary': summary, 'next_action': action, 'evidence': evidence, 'created': created})
        run_text = tx.encoded(run)
        limit = MAX_RUN_BYTES if phase == 'end' else MAX_RUN_BYTES - END_RESERVE_BYTES
        require(len(run_text.encode('utf-8')) <= limit, 'Run byte budget reached; end this run before starting another.', 'RUN_LIMIT_REACHED')
        files[run_path] = (old_run, run_text)
        if tx.encoded(state) != old_state:
            files['data/harness.json'] = (old_state, tx.encoded(state))
        self._validate_harness(records, state, run)
        return {'id': run_id, 'issue': run['issue'], 'status': run['status'], 'version': ix.digest(files[run_path][1])}
