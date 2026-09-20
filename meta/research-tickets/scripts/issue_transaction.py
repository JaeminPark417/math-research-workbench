"""Durable, recoverable transactions for cooperating Research Desk clients.

The project lock is mandatory. External editors are not locked; unknown edits
halt recovery. Receipts are canonical; full recovery copies are local history.
"""
import datetime as dt
import json
import os
import ticket_fs as fs
from pathlib import Path
import re

from issue_index import canonical, digest, fail, json_read, IndexErrorDetail

PENDING = 'data/transactions/pending.json'
MAX_JOURNAL_BYTES = 32 * 1024 * 1024
KEY_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def key(value):
    if not isinstance(value, str) or not KEY_RE.fullmatch(value):
        fail('INVALID_ARGUMENT', 'Operation/run keys must be 1–64 ASCII letters, digits, underscores or hyphens.')
    return value


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def optional(index, path, maximum=MAX_JOURNAL_BYTES):
    try:
        return index._read(path, maximum).decode('utf-8')
    except FileNotFoundError:
        return None
    except UnicodeError:
        fail('INVALID_DATA', 'Stored data must use UTF-8.', path=path)


def ensure_dir(index, relative):
    current = Path()
    for part in Path(relative).parts:
        current /= part
        try:
            index._checked(str(current), directory=True)
        except FileNotFoundError:
            (index.root / current).mkdir(exist_ok=True)
            index._checked(str(current), directory=True)
            parent = index.root / current.parent
            fd = fs.open_dir(parent)
            try:
                fs.sync_dir(fd)
            finally:
                fs.close_dir(fd)


def atomic(index, path, text, before):
    """Publish complete UTF-8 text, without clobbering a concurrently created file."""
    index._assert_lock_current()
    parent, name = str(Path(path).parent), Path(path).name
    ensure_dir(index, parent)
    directory = index._checked(parent, directory=True)
    dirfd = fs.open_dir(directory)
    temp = '.desk-' + os.urandom(12).hex() + '.tmp'
    try:
        fd = fs.open_file(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, parent=dirfd)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(text.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        if optional(index, path) != before:
            fail('CONFLICT', 'File changed before publication; no overwrite was performed.', path=path)
        index._assert_lock_current()
        if before is None:
            fs.link(temp, name, dirfd)
        else:
            fs.replace(temp, name, dirfd)
        fs.sync_dir(dirfd)
    finally:
        try:
            fs.unlink(temp, dirfd)
        except FileNotFoundError:
            pass
        fs.close_dir(dirfd)


def target_path(path):
    return isinstance(path, str) and (path in ('data/relations.json', 'data/harness.json') or
        re.fullmatch(r'data/issues/res-[0-9]+\.md', path) is not None or
        re.fullmatch(r'data/(?:runs|operations)/[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.json', path) is not None)


def read_pending(index):
    raw = optional(index, PENDING)
    if raw is None:
        return None, None
    journal = json_read(raw, PENDING)
    if not isinstance(journal, dict):
        fail('INVALID_JOURNAL', 'Pending transaction is malformed; preserved for inspection.')
    checksum = journal.pop('checksum', None)
    if checksum != digest(canonical(journal)) or journal.get('schema') != 1:
        fail('INVALID_JOURNAL', 'Pending transaction checksum/schema mismatch; no sources changed.')
    if not isinstance(journal.get('request_hash'), str) or not re.fullmatch('[0-9a-f]{64}', journal['request_hash']) or not isinstance(journal.get('result'), dict):
        fail('INVALID_JOURNAL', 'Pending transaction request/receipt metadata is malformed.')
    key(journal.get('operation_id'))
    entries = journal.get('files')
    if not isinstance(entries, list) or not 1 <= len(entries) <= 32:
        fail('INVALID_JOURNAL', 'Invalid transaction file list.')
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'path', 'before', 'after'} or not target_path(entry['path']):
            fail('INVALID_JOURNAL', 'Transaction contains an unsupported path.')
        if entry['path'] in seen or not isinstance(entry['after'], str) or entry['before'] is not None and not isinstance(entry['before'], str):
            fail('INVALID_JOURNAL', 'Invalid transaction contents.')
        seen.add(entry['path'])
    if entries[-1]['path'] != 'data/operations/' + journal['operation_id'] + '.json':
        fail('INVALID_JOURNAL', 'The durable receipt must be published last.')
    return journal, raw


def receipt(index, operation_id):
    raw = optional(index, 'data/operations/' + key(operation_id) + '.json')
    if raw is None:
        return None
    value = json_read(raw, 'operation receipt')
    if not isinstance(value, dict) or value.get('schema') != 1 or value.get('operation_id') != operation_id or value.get('status') not in ('applied', 'abandoned') or not isinstance(value.get('request_hash'), str) or not isinstance(value.get('result'), dict):
        fail('INVALID_DATA', 'Invalid durable operation receipt.', operation_id=operation_id)
    return value


def archive_pending(index, journal, raw):
    ensure_dir(index, 'data/history')
    destination = 'data/history/' + journal['operation_id'] + '.json'
    previous = optional(index, destination)
    if previous is not None and previous != raw:
        fail('RECOVERY_CONFLICT', 'Recovery history key already exists.', path=destination)
    if previous is None:
        atomic(index, destination, raw, None)
    if optional(index, PENDING) != raw:
        fail('RECOVERY_CONFLICT', 'Pending journal changed while archiving.')
    index._assert_lock_current()
    directory = index._checked('data/transactions', directory=True)
    fd = fs.open_dir(directory)
    try:
        fs.unlink('pending.json', fd)  # Full journal is now preserved in history.
        fs.sync_dir(fd)
    finally:
        fs.close_dir(fd)


def status(index):
    journal, raw = read_pending(index)
    if journal is None:
        return {'ok': True, 'pending': False}
    files = []
    for entry in journal['files']:
        current = optional(index, entry['path'])
        state = 'after' if current == entry['after'] else 'before' if current == entry['before'] else 'conflict'
        files.append({'path': entry['path'], 'state': state,
                      'current_hash': digest(current) if current is not None else None})
    return {'ok': True, 'pending': True, 'operation_id': journal['operation_id'],
            'journal_hash': digest(raw), 'files': files}


def finish(index, expected_journal=None):
    journal, raw = read_pending(index)
    if journal is None:
        return {'ok': True, 'pending': False}
    if expected_journal is not None and expected_journal != digest(raw):
        fail('CONFLICT', 'Pending journal changed since inspection.')
    final = receipt(index, journal['operation_id'])
    if final:
        if final['request_hash'] != journal['request_hash']:
            fail('RECOVERY_CONFLICT', 'Operation receipt disagrees with the pending transaction.')
        archive_pending(index, journal, raw)
        return {'ok': True, 'pending': False, 'status': final['status'], 'operation_id': journal['operation_id']}
    # Check every target before changing any target. Never hide external edits.
    for entry in journal['files']:
        if optional(index, entry['path']) not in (entry['before'], entry['after']):
            fail('RECOVERY_CONFLICT', 'Unknown edit blocks recovery; use recover status and preserve/merge the edit.', path=entry['path'])
    for entry in journal['files']:
        current = optional(index, entry['path'])
        if current == entry['after']:
            continue
        if current != entry['before']:
            fail('RECOVERY_CONFLICT', 'File changed during recovery.', path=entry['path'])
        atomic(index, entry['path'], entry['after'], entry['before'])
    archive_pending(index, journal, raw)
    return {'ok': True, 'pending': False, 'status': 'applied', 'operation_id': journal['operation_id']}


def commit(index, operation_id, request_hash, files, result):
    ensure_dir(index, 'data/history')
    ensure_dir(index, 'data/transactions')
    ensure_dir(index, 'data/operations')
    if optional(index, PENDING) is not None:
        fail('PENDING_TRANSACTION', 'Finish the pending transaction before another write.')
    stamp = now()
    record = {'schema': 1, 'operation_id': operation_id, 'request_hash': request_hash,
              'status': 'applied', 'at': stamp, 'result': result}
    entries = [{'path': path, 'before': pair[0], 'after': pair[1]} for path, pair in sorted(files.items()) if pair[0] != pair[1]]
    entries.append({'path': 'data/operations/' + operation_id + '.json', 'before': None, 'after': encoded(record)})
    journal = {'schema': 1, 'operation_id': operation_id, 'request_hash': request_hash, 'at': stamp,
               'files': entries, 'result': result,
               'before': next((e['before'] for e in entries if e['path'].startswith('data/issues/')), None)}
    journal['checksum'] = digest(canonical(journal))
    raw = encoded(journal)
    if len(raw.encode('utf-8')) > MAX_JOURNAL_BYTES or len(entries) > 32:
        fail('TRANSACTION_TOO_LARGE', 'Transaction exceeds 32 MiB or 32 files; split the work before writing.')
    for entry in entries:
        if optional(index, entry['path']) != entry['before']:
            fail('CONFLICT', 'Source changed before transaction preparation.', path=entry['path'])
    atomic(index, PENDING, raw, None)
    try:
        finish(index)
    except (OSError, IndexErrorDetail) as error:
        fail('TRANSACTION_PENDING', 'Prepared transaction needs recovery; do not submit a different operation to overwrite it.',
             operation_id=operation_id, cause=getattr(error, 'code', 'FILESYSTEM_ERROR'))
    return result


def keep_current(index, expected_journal, expected_files, validate_current):
    """Explicit escape hatch: preserve a coherent current state and abandon the plan."""
    journal, raw = read_pending(index)
    if journal is None or expected_journal != digest(raw):
        fail('CONFLICT', 'Inspect the current pending journal before accepting current files.')
    current = status(index)
    actual = {f['path']: f['current_hash'] for f in current['files']}
    if not isinstance(expected_files, dict) or expected_files != actual:
        fail('CONFLICT', 'Current file hashes differ from the explicitly reviewed state.')
    if receipt(index, journal['operation_id']):
        fail('INVALID_ARGUMENT', 'This transaction already has a final receipt; finish its journal cleanup instead.')
    validate_current()
    # Validate a second time at the publication boundary.
    if {f['path']: f['current_hash'] for f in status(index)['files']} != actual:
        fail('CONFLICT', 'Files changed during current-state validation.')
    final = {'schema': 1, 'operation_id': journal['operation_id'], 'request_hash': journal['request_hash'],
             'status': 'abandoned', 'at': now(), 'result': {'preserved_current_hashes': actual}}
    atomic(index, 'data/operations/' + journal['operation_id'] + '.json', encoded(final), None)
    archive_pending(index, journal, raw)
    return {'ok': True, 'pending': False, 'status': 'abandoned', 'operation_id': journal['operation_id']}
