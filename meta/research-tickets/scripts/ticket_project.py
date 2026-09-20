"""Explicit, local-only enrollment of project capsules or existing paper notes."""
import json
import os
import ticket_fs as fs
from pathlib import Path
import re
import tempfile

import issue_index as ix


def validate_config(config):
    required = {'schema', 'project_id', 'coverage', 'repositories'}
    if not isinstance(config, dict) or not required <= set(config) or set(config) - required - {'subject'} or type(config['schema']) is not int or config['schema'] != 1:
        ix.fail('INVALID_CONFIG', 'Registration needs schema=1, project_id, coverage and repositories.')
    if not isinstance(config['project_id'], str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}', config['project_id']):
        ix.fail('INVALID_CONFIG', 'Use the project directory slug as project_id.')
    coverage = config['coverage']
    if not isinstance(coverage, dict) or set(coverage) != {'state', 'scope', 'untracked'} or coverage['state'] not in ('partial', 'complete') or not ix._text(coverage['scope'], 2000) or not isinstance(coverage['untracked'], list) or len(coverage['untracked']) > 50 or any(not ix._text(s, 2000) for s in coverage['untracked']):
        ix.fail('INVALID_CONFIG', 'Coverage must describe scope and remaining untracked work.')
    if coverage['state'] == 'complete' and coverage['untracked']:
        ix.fail('INVALID_CONFIG', 'Complete coverage cannot list untracked work.')
    repos = config['repositories']
    if not isinstance(repos, dict) or len(repos) > 10:
        ix.fail('INVALID_CONFIG', 'Use at most ten explicitly registered repositories.')
    for key, repo in repos.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', key) or key == 'capsule' or not isinstance(repo, dict) or set(repo) != {'path', 'origin'} or not isinstance(repo['path'], str) or not Path(repo['path']).is_absolute() or not ix._text(repo['origin'], 2000):
            ix.fail('INVALID_CONFIG', 'Repository registration needs a name, absolute path and expected origin.')
        from issue_sources import _origin
        _origin(repo['origin'])
    if 'subject' in config:
        subject = config['subject']
        if not isinstance(subject, dict) or set(subject) != {'kind', 'note', 'extracts'} or subject['kind'] != 'paper':
            ix.fail('INVALID_CONFIG', 'Subject needs kind, note and extracts; kind must be the literal paper for both paper and book notes.')
        if (subject['note'] != config['project_id'] + '.md'
                or not isinstance(subject['extracts'], list) or len(subject['extracts']) > 50
                or any(not isinstance(p, str) for p in subject['extracts'])
                or len(set(subject['extracts'])) != len(subject['extracts'])
                or 'paper' in repos):
            ix.fail('INVALID_CONFIG', 'Paper subject needs its exact note, distinct extract paths and an unshadowed paper alias.')
        from issue_sources import _source_path
        try:
            _source_path(subject['note'])
            for value in subject['extracts']:
                path = _source_path(value)
                if path.parts[0] != 'content' or len(path.parts) < 2 or 'tickets' in [p.lower() for p in path.parts]:
                    ix.fail('INVALID_CONFIG', 'Paper extracts must be explicit text files under content/, outside ticket stores.')
        except ix.IndexErrorDetail:
            ix.fail('INVALID_CONFIG', 'Paper note/extract paths must be safe, relative text-source paths.')
    return config


def _paper_note(value):
    """Inspect only an explicit real note; no slugification or YAML inference."""
    note = Path(value).expanduser().absolute()
    if note.resolve() != note:
        ix.fail('INVALID_PAPER', 'Use the canonical paper path without symbolic-link components or traversal.')
    if note.suffix != '.md' or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}', note.stem):
        ix.fail('INVALID_PAPER', 'Select a .md paper note with a lowercase, hyphenated filename.')
    from issue_sources import _read_file, _source_path
    _source_path(note.name)
    raw = _read_file(note.parent, note.name)
    try:
        lines = raw.decode('utf-8').splitlines()
        end = lines.index('---', 1) if lines and lines[0] == '---' else 0
    except (UnicodeError, ValueError):
        ix.fail('INVALID_PAPER', 'Paper note needs closed UTF-8 YAML frontmatter.')
    type_key = r'''(?:type|'type'|"type")'''
    types = [line for line in lines[1:end] if re.match('^' + type_key + r'\s*:', line)]
    if len(types) != 1 or not re.fullmatch(type_key + r'''\s*:\s*(?:paper|book|'paper'|'book'|"paper"|"book")(?:\s+#.*)?\s*''', types[0]):
        ix.fail('INVALID_PAPER', 'Select a note whose single frontmatter type is paper or book.')
    return note, ix.digest(raw)


def validate_paper_registration(root, config, display=None):
    """Enforce identity for selectors, direct index users and source resolution."""
    validate_config(config)
    root = Path(root).absolute()
    if ('subject' not in config or root.resolve() != root or root.name != 'tickets'
            or root.parent.name != config['project_id']):
        ix.fail('INVALID_CONFIG', 'Paper registration and store location do not agree.')
    note, _ = _paper_note(root.parent.parent / config['subject']['note'])
    if display is None:
        from issue_sources import _read_file
        display = ix.json_read(_read_file(root, 'data/project.json', 65536), 'paper display metadata')
    if not isinstance(display, dict) or display.get('id') != note.stem:
        ix.fail('INVALID_CONFIG', 'Paper display identity does not match the selected note.')
    return note


def _write_initial(root, identifier, name, config):
    (root / 'data/issues').mkdir(parents=True)
    for path, content in {'project.json': config,
                          'data/project.json': {'id': identifier, 'name': name or identifier, 'source_url': None, 'mode': 'local'},
                          'data/relations.json': []}.items():
        with (root / path).open('x', encoding='utf-8') as stream:
            json.dump(content, stream, ensure_ascii=False, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def load_paper(value):
    note, _ = _paper_note(value)
    root = note.with_suffix('') / 'tickets'
    if not (root / 'project.json').exists():
        ix.fail('NOT_CONFIGURED', 'Paper has not been enrolled; use init only for a requested paper workflow.')
    from issue_sources import _read_file
    config = ix.json_read(_read_file(root, 'project.json', 65536), 'paper registration')
    if validate_paper_registration(root, config) != note:
        ix.fail('INVALID_CONFIG', 'Registration belongs to another paper.')
    return root, config


def initialize_paper(value, name=None, config=None):
    """Publish a complete new support directory; never edit the selected note."""
    note, before = _paper_note(value)
    support = note.with_suffix('')
    config = validate_config(config if config is not None else {
        'schema': 1, 'project_id': note.stem,
        'coverage': {'state': 'partial', 'scope': 'Selected paper reading; claim map not yet inventoried.',
                     'untracked': ['Statements, proofs, citations and appendices outside the selected reading scope.']},
        'repositories': {}, 'subject': {'kind': 'paper', 'note': note.name, 'extracts': []}})
    if config['project_id'] != note.stem or config.get('subject', {}).get('note') != note.name:
        ix.fail('INVALID_CONFIG', 'Paper registration must identify the selected note.')
    if len((json.dumps(config, ensure_ascii=False, indent=2) + '\n').encode('utf-8')) > 65536:
        ix.fail('INVALID_CONFIG', 'Registration exceeds 64 KiB.')
    if name is not None and not ix._text(name, 1000):
        ix.fail('INVALID_ARGUMENT', 'Paper display name must be nonempty and at most 1000 characters.')
    if support.exists() or support.is_symlink():
        ix.fail('ALREADY_CONFIGURED', 'Paper support path already exists; inspect it instead of adopting or overwriting it.')
    with tempfile.TemporaryDirectory(prefix='.ticket-paper-init-', dir=note.parent) as temporary:
        staged = Path(temporary) / note.stem
        _write_initial(staged / 'tickets', note.stem, name, config)
        import stat
        lock = note.parent / '.ticket-enrollment.lock'
        fd = fs.open_file(lock, os.O_CREAT | os.O_RDWR)
        try:
            held = os.fstat(fd)
            if not stat.S_ISREG(held.st_mode):
                ix.fail('UNSAFE_PATH', 'Enrollment lock must be a regular file.')
            try:
                fs.try_lock(fd)
            except BlockingIOError:
                ix.fail('INDEX_BUSY', 'Another initializer is enrolling a paper.')
            current = lock.lstat()
            if (current.st_dev, current.st_ino) != (held.st_dev, held.st_ino):
                ix.fail('LOCK_REPLACED', 'Enrollment lock changed; do not remove lock files.')
            if _paper_note(note)[1] != before:
                ix.fail('SOURCE_CHANGED', 'Paper note changed during enrollment.')
            if support.exists() or support.is_symlink():
                ix.fail('ALREADY_CONFIGURED', 'Another initializer created the paper support path.')
            staged.rename(support)
            parent_fd = fs.open_dir(note.parent)
            try:
                fs.sync_dir(parent_fd)
            finally:
                fs.close_dir(parent_fd)
        finally:
            os.close(fd)
    return {'ok': True, 'paper': str(note), 'root': str(support / 'tickets'),
            'coverage': config['coverage'], 'issues': 0}


def project_path(value):
    path = Path(value).expanduser().absolute()
    if path.resolve() != path or not path.is_dir() or (path / 'README.md').is_symlink() or not (path / 'README.md').is_file():
        ix.fail('INVALID_PROJECT', 'Select a real project capsule directory with README.md; symlinks are not accepted.')
    return path


def load_project(value):
    project = project_path(value)
    root = project / 'tickets'
    registration = root / 'project.json'
    if not registration.exists():
        ix.fail('NOT_CONFIGURED', 'Project has not been migrated. Read its capsule; use init only for an explicitly requested enrollment.', project=str(project))
    if root.is_symlink() or registration.is_symlink():
        ix.fail('UNSAFE_PATH', 'Ticket registration cannot be a symlink.')
    if registration.stat().st_size > 65536:
        ix.fail('INVALID_CONFIG', 'Registration exceeds 64 KiB.')
    config = validate_config(ix.json_read(registration.read_bytes(), 'ticket registration'))
    if config['project_id'] != project.name or 'subject' in config:
        ix.fail('INVALID_CONFIG', 'Registration belongs to another project.')
    return root, config


def initialize(value, name=None, config=None):
    project = project_path(value)
    root = project / 'tickets'
    if root.exists() or root.is_symlink():
        ix.fail('ALREADY_CONFIGURED', 'The tickets path already exists; inspect it instead of overwriting.')
    config = validate_config(config if config is not None else {'schema': 1, 'project_id': project.name,
        'coverage': {'state': 'partial', 'scope': 'New local ticket store; project migration pending.',
                     'untracked': ['Existing capsule Next steps and research-run ledgers have not been indexed.']}, 'repositories': {}})
    if config['project_id'] != project.name or 'subject' in config:
        ix.fail('INVALID_CONFIG', 'Registration belongs to another project.')
    if len((json.dumps(config, ensure_ascii=False, indent=2) + '\n').encode('utf-8')) > 65536:
        ix.fail('INVALID_CONFIG', 'Registration exceeds 64 KiB.')
    if name is not None and not ix._text(name, 1000):
        ix.fail('INVALID_ARGUMENT', 'Project name must be nonempty and at most 1000 characters.')
    # Build away from the live path. Failed preparation never leaves an active registration.
    with tempfile.TemporaryDirectory(prefix='.ticket-init-', dir=project) as temporary:
        staged = Path(temporary) / 'tickets'
        _write_initial(staged, project.name, name, config)
        # mkdir is exclusive; rename into it would overwrite an empty directory, so use a
        # stable parent-side lock to serialize cooperating initializers and recheck.
        lock_path = project / '.ticket-enrollment.lock'
        fd = fs.open_file(lock_path, os.O_CREAT | os.O_RDWR)
        try:
            import stat
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                ix.fail('UNSAFE_PATH', 'Enrollment lock must be a regular file.')
            try:
                fs.try_lock(fd)
            except BlockingIOError:
                ix.fail('INDEX_BUSY', 'Another initializer is enrolling this capsule.')
            if root.exists() or root.is_symlink():
                ix.fail('ALREADY_CONFIGURED', 'Another initializer created the tickets path.')
            staged.rename(root)
            parent_fd = fs.open_dir(project)
            try:
                fs.sync_dir(parent_fd)
            finally:
                fs.close_dir(parent_fd)
        finally:
            os.close(fd)
    return {'ok': True, 'project': project.name, 'root': str(root), 'coverage': config['coverage'], 'issues': 0}
