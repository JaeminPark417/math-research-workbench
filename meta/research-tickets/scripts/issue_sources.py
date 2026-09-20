"""Bounded, read-only source references for local research tickets.

A verified reference certifies bytes and (optionally) a Markdown heading. It
does not certify a proof, human promotion, or that a commit has been pushed.
Only explicitly registered repositories are opened; no network is used.
"""
from __future__ import annotations

import hashlib
import os
import ticket_fs as fs
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from urllib.parse import urlsplit

import issue_index as ix

MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_CONFIG_BYTES = 256 * 1024
FIELDS = {'repository', 'mode', 'commit', 'path', 'sha256', 'heading', 'object_id'}
TEXT_SUFFIXES = {'.md', '.markdown', '.txt', '.json', '.tex', '.lean', '.py',
                 '.csv', '.rst', '.yaml', '.yml', '.toml'}
NAME_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z')
COMMIT_RE = re.compile(r'[0-9a-f]{40}\Z')
HASH_RE = re.compile(r'[0-9a-f]{64}\Z')
SECRET_RE = re.compile(r'(?:credentials?|secrets?|tokens?|passwords?|api[-_]?keys?)(?:[._-]|$)', re.I)
DENIED_NAMES = {'.git', '.ssh', '.aws', '.gnupg', '.netrc', '.npmrc', '.pypirc',
                'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519', 'auth.json', 'auth.yaml'}


def _short_text(value, limit):
    return (isinstance(value, str) and bool(value.strip()) and len(value) <= limit
            and not any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value))


def _source_path(value):
    if not _short_text(value, 2000) or '\\' in value or ':' in value:
        ix.fail('INVALID_ARGUMENT', 'Source path must be a bounded relative POSIX path.')
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(p in ('', '.', '..') for p in value.split('/')):
        ix.fail('INVALID_ARGUMENT', 'Source path must be relative without traversal or normalization.')
    if (any(p.lower() in DENIED_NAMES or p.lower().startswith('.env') or SECRET_RE.match(p)
            for p in path.parts) or path.suffix.lower() not in TEXT_SUFFIXES):
        ix.fail('SOURCE_POLICY', 'Source path is excluded from research references.')
    return path


def validate_reference(ref):
    """Validate shape without opening a file; return a detached normalized dict."""
    if not isinstance(ref, dict) or set(ref) - FIELDS or not {'repository', 'mode', 'path', 'sha256'} <= set(ref):
        ix.fail('INVALID_ARGUMENT', 'Invalid source reference fields.')
    if not isinstance(ref['repository'], str) or not NAME_RE.fullmatch(ref['repository']):
        ix.fail('INVALID_ARGUMENT', 'Invalid source repository name.')
    if ref['mode'] not in ('commit', 'working'):
        ix.fail('INVALID_ARGUMENT', 'Source mode must be commit or working.')
    if not isinstance(ref['sha256'], str) or not HASH_RE.fullmatch(ref['sha256']):
        ix.fail('INVALID_ARGUMENT', 'Source reference requires a lowercase SHA-256 hash.')
    _source_path(ref['path'])
    if ref['mode'] == 'commit':
        if not isinstance(ref.get('commit'), str) or not COMMIT_RE.fullmatch(ref['commit']):
            ix.fail('INVALID_ARGUMENT', 'Committed sources require a full lowercase 40-character commit ID.')
        if ref['repository'] == 'capsule':
            ix.fail('INVALID_ARGUMENT', 'Capsule references support working snapshots only.')
    elif 'commit' in ref:
        ix.fail('INVALID_ARGUMENT', 'Working snapshots must not claim a commit.')
    for field in ('heading', 'object_id'):
        if field in ref and not _short_text(ref[field], 1000 if field == 'heading' else 200):
            ix.fail('INVALID_ARGUMENT', 'Invalid source annotation.', field=field)
    return dict(ref)


def _read_file(base, relative, limit=MAX_SOURCE_BYTES):
    """Open each component without following links, including during renames."""
    descriptors = []
    fd = None
    try:
        descriptors.append(fs.open_dir(base))
        parts = PurePosixPath(relative).parts
        for part in parts[:-1]:
            descriptors.append(fs.open_dir(part, parent=descriptors[-1]))
        fd = fs.open_file(parts[-1], os.O_RDONLY, parent=descriptors[-1])
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            ix.fail('SOURCE_POLICY', 'Sources must be regular files.')
        if before.st_size > limit:
            ix.fail('SOURCE_TOO_LARGE', 'Source exceeds the permitted byte limit.')
        chunks, total = [], 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                ix.fail('SOURCE_TOO_LARGE', 'Source exceeds the permitted byte limit.')
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            ix.fail('SOURCE_MISMATCH', 'Source changed during the read.')
        return b''.join(chunks)
    except OSError:
        ix.fail('SOURCE_UNAVAILABLE', 'Source is missing, inaccessible, or traverses a symbolic link.')
    finally:
        if fd is not None:
            os.close(fd)
        for directory in reversed(descriptors):
            fs.close_dir(directory)


def _config(root):
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        ix.fail('SOURCE_POLICY', 'Ticket store root must be a real directory.')
    config = ix.json_read(_read_file(root, 'project.json', MAX_CONFIG_BYTES), 'project.json')
    if (not isinstance(config, dict) or type(config.get('schema')) is not int or config['schema'] != 1
            or not _short_text(config.get('project_id'), 200)
            or not isinstance(config.get('repositories'), dict)):
        ix.fail('INVALID_DATA', 'Invalid ticket project source registry.')
    if 'subject' in config:
        from ticket_project import validate_paper_registration
        validate_paper_registration(root, config)
    return root, config


def _origin(value):
    """Accept credential-free remotes; normalize GitHub SSH/HTTPS equivalence."""
    if not _short_text(value, 2000):
        ix.fail('SOURCE_POLICY', 'Repository origin must be a credential-free remote URL.')
    scp = re.fullmatch(r'git@([A-Za-z0-9.-]+):([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?', value)
    if scp:
        host, path = scp[1].lower(), scp[2]
        if host == 'github.com':
            return ('github.com', path.removesuffix('.git').lower())
        return ('exact', value)
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in ('https', 'ssh') or not parsed.hostname or parsed.password
                or parsed.query or parsed.fragment
                or parsed.username is not None and not (parsed.scheme == 'ssh' and parsed.username == 'git')
                or not re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?', parsed.path)):
            raise ValueError()
        if parsed.hostname.lower() == 'github.com' and parsed.port is None:
            return ('github.com', parsed.path.strip('/').removesuffix('.git').lower())
        return ('exact', value)
    except (ValueError, TypeError):
        ix.fail('SOURCE_POLICY', 'Repository origin must be a credential-free remote URL.')


def _git(base, *args, limit=MAX_SOURCE_BYTES):
    # Ambient GIT_DIR, replacement refs, and global URL rewrites must not select
    # another repository or alter the content addressed by the recorded commit.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    try:
        result = subprocess.run(['git', '--no-pager', '--literal-pathspecs', '-C', str(base), *args],
                                capture_output=True, env=env, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        ix.fail('SOURCE_UNAVAILABLE', 'Cannot inspect the registered Git repository.')
    if result.returncode:
        # Never expose stderr: a Git error can contain an origin or local secret.
        ix.fail('SOURCE_UNAVAILABLE', 'Cannot resolve the registered repository or requested Git object.')
    if len(result.stdout) > limit:
        ix.fail('SOURCE_TOO_LARGE', 'Git source exceeds the permitted byte limit.')
    return result.stdout


def _repository(root, name, config=None):
    if config is None:
        root, config = _config(root)
    if name == 'capsule':
        return root.parent.resolve()
    if name == 'paper' and 'subject' in config:
        return root.parent.parent
    registration = config['repositories'].get(name)
    if not isinstance(registration, dict) or set(registration) != {'path', 'origin'}:
        ix.fail('SOURCE_POLICY', 'Source repository is not registered with an exact path and origin.')
    expected = _origin(registration['origin'])
    path = registration['path']
    if not _short_text(path, 4096) or not Path(path).is_absolute() or Path(path).is_symlink():
        ix.fail('SOURCE_POLICY', 'Registered repository root must be an absolute real directory.')
    base = Path(path)
    if base != base.resolve():
        ix.fail('SOURCE_POLICY', 'Registered repository root must use its real path without symbolic-link ancestors.')
    try:
        actual_root = Path(_git(base, 'rev-parse', '--show-toplevel', limit=8192).decode('utf-8').strip())
        actual_origin = _git(base, 'config', '--local', '--get', 'remote.origin.url', limit=8192).decode('utf-8').strip()
    except UnicodeError:
        ix.fail('SOURCE_POLICY', 'Repository identity must use UTF-8.')
    if actual_root.resolve() != base.resolve() or _origin(actual_origin) != expected:
        ix.fail('SOURCE_POLICY', 'Registered repository root or origin does not match.')
    return base.resolve()


def _content(root, ref):
    # A logical paper alias is local text only. Reject before repository/Git
    # resolution; an old project with a Git alias named paper remains supported.
    root, config = _config(root)
    if ref['repository'] == 'paper' and 'subject' in config:
        subject = config['subject']
        if ref['mode'] != 'working' or ref['path'] not in [subject['note']] + subject['extracts']:
            ix.fail('SOURCE_POLICY', 'Paper sources require working mode and an explicitly registered note or extract.')
    base = _repository(root, ref['repository'], config)
    path = _source_path(ref['path'])
    if ref['repository'] == 'capsule':
        if path.parts[0].lower() == 'tickets' or path.parts[0] == Path(root).name:
            ix.fail('SOURCE_POLICY', 'Capsule sources cannot recursively reference their ticket store.')
    if ref['mode'] == 'working':
        raw = _read_file(base, str(path))
    else:
        commit = ref['commit']
        if _git(base, 'cat-file', '-t', commit, limit=100).strip() != b'commit':
            ix.fail('SOURCE_POLICY', 'Recorded revision must name a commit object.')
        tree = _git(base, 'ls-tree', '-z', commit, '--', str(path), limit=8192)
        entries = tree.rstrip(b'\x00').split(b'\x00') if tree else []
        if len(entries) != 1:
            ix.fail('SOURCE_UNAVAILABLE', 'Source path does not name one file at the recorded commit.')
        try:
            properties, name = entries[0].split(b'\t', 1)
            mode, kind, object_id = properties.split(b' ')
        except ValueError:
            ix.fail('SOURCE_UNAVAILABLE', 'Invalid Git tree response.')
        if mode not in (b'100644', b'100755') or kind != b'blob' or name != str(path).encode('utf-8'):
            ix.fail('SOURCE_POLICY', 'Committed source must be a regular file, not a link, tree, or submodule.')
        try:
            size = int(_git(base, 'cat-file', '-s', object_id.decode('ascii'), limit=100))
        except (ValueError, UnicodeError):
            ix.fail('SOURCE_UNAVAILABLE', 'Invalid Git object size.')
        if size < 0 or size > MAX_SOURCE_BYTES:
            ix.fail('SOURCE_TOO_LARGE', 'Committed source exceeds the permitted byte limit.')
        raw = _git(base, 'cat-file', 'blob', object_id.decode('ascii'))
        if len(raw) != size:
            ix.fail('SOURCE_MISMATCH', 'Git object size changed during verification.')
    try:
        text = raw.decode('utf-8')
        if '\x00' in text:
            raise UnicodeError()
    except UnicodeError:
        ix.fail('SOURCE_POLICY', 'Research sources must be UTF-8 text without NUL bytes.')
    return raw, text


def _check_heading(ref, text):
    if 'heading' not in ref:
        return
    if PurePosixPath(ref['path']).suffix.lower() not in {'.md', '.markdown'}:
        ix.fail('INVALID_ARGUMENT', 'Heading anchors currently require a Markdown source.')
    wanted = re.sub(r'^#{1,6}\s+', '', ref['heading'].strip()).strip()
    headings, fence, math_close, previous = [], None, None, None
    lines = text.splitlines()
    if lines and lines[0] == '---':
        try:
            end = lines.index('---', 1)
        except ValueError:
            pass  # A generic Markdown source may start with a horizontal rule.
        else:
            lines = lines[end + 1:]
    for line in lines:
        stripped = line.strip()
        if fence:
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(fence[1]) + r',}\s*', line):
                fence = None
            continue
        if math_close:
            if stripped == math_close:
                math_close = None
            continue
        delimiter = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if delimiter:
            fence = (delimiter[1][0], len(delimiter[1]))
            previous = None
            continue
        if stripped in ('$$', '\\['):
            math_close = '$$' if stripped == '$$' else '\\]'
            previous = None
            continue
        match = re.match(r'^ {0,3}#{1,6}\s+(.+?)\s*$', line)
        if match:
            headings.append(re.sub(r'\s+#+\s*$', '', match[1]).strip())
            previous = None
        elif previous and re.fullmatch(r' {0,3}(?:=+|-+)\s*', line):
            headings.append(previous)
            previous = None
        else:
            previous = stripped or None
    count = headings.count(wanted)
    if count != 1:
        ix.fail('SOURCE_MISMATCH', 'Selected heading must occur exactly once in the referenced source.')


def verify_reference(root, ref):
    """Verify registered identity, exact bytes, and heading; return the reference."""
    ref = validate_reference(ref)
    raw, text = _content(root, ref)
    if hashlib.sha256(raw).hexdigest() != ref['sha256']:
        ix.fail('SOURCE_MISMATCH', 'Source bytes do not match the recorded SHA-256 hash.')
    _check_heading(ref, text)
    return ref


def snapshot(root, repository, path, commit=None, heading=None):
    """Create a reference without writing it or claiming proof/publication status."""
    ref = {'repository': repository, 'mode': 'commit' if commit is not None else 'working',
           'path': path, 'sha256': '0' * 64}
    if commit is not None:
        ref['commit'] = commit
    if heading is not None:
        ref['heading'] = heading
    ref = validate_reference(ref)
    raw, text = _content(root, ref)
    _check_heading(ref, text)
    ref['sha256'] = hashlib.sha256(raw).hexdigest()
    return ref


def check_drift(root, ref):
    """Compare a valid historical reference with current working bytes read-only."""
    ref = validate_reference(ref)
    historical = {}
    if ref['mode'] == 'commit':
        try:
            verify_reference(root, ref)
        except ix.IndexErrorDetail as error:
            return {'state': 'unavailable', 'reference_state': 'unavailable', 'reason': error.code}
        # Preserve the established working-tree drift state while distinguishing
        # the independently verified immutable evidence from current files.
        historical['reference_state'] = 'verified'
    try:
        current = snapshot(root, ref['repository'], ref['path'])
        return {'state': 'current' if current['sha256'] == ref['sha256'] else 'changed',
                'sha256': current['sha256'], **historical}
    except ix.IndexErrorDetail as error:
        return {'state': 'unavailable', 'reason': error.code, **historical}
