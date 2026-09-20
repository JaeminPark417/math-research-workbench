#!/usr/bin/env python3
"""JSON CLI for Workbench research tickets. No server, network, or model required."""
import sys
sys.dont_write_bytecode = True
import argparse
import json
from pathlib import Path
from issue_index import IssueIndex, IndexErrorDetail, DEFAULT_FIELDS
from issue_store import IssueStore
from issue_index import json_read


def request_file(path):
    with (open(path, 'rb') if path != '-' else sys.stdin.buffer) as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise IndexErrorDetail('INVALID_ARGUMENT', 'Request exceeds 4 MiB.')
    return json_read(raw, 'request file')


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise IndexErrorDetail('INVALID_ARGUMENT', message)


def main(argv=None):
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = Parser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--project', help='Project capsule directory; tickets live in its tickets/ subdirectory')
    target.add_argument('--paper', help='Existing paper/book Markdown note; tickets live in a sibling support directory')
    target.add_argument('--root', help='Explicit legacy/test store root (does not enroll a project)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='Explicitly enroll an existing capsule or paper note with zero issues')
    p.add_argument('--name')
    p.add_argument('--config-file')
    sub.add_parser('doctor', help='Check registration, source schemas and harness consistency')
    p = sub.add_parser('source')
    source = p.add_subparsers(dest='action', required=True)
    s = source.add_parser('snapshot')
    s.add_argument('repository')
    s.add_argument('path')
    s.add_argument('--commit')
    s.add_argument('--heading')
    s.add_argument('--object-id')
    s = source.add_parser('check')
    s.add_argument('id', nargs='+')
    s.add_argument('--limit', type=int, default=20)
    s.add_argument('--cursor')
    for name in ('list', 'search'):
        p = sub.add_parser(name)
        if name == 'search':
            p.add_argument('query')
        for flag in ('kind', 'status', 'parent', 'outcome'):
            p.add_argument('--' + flag)
        p.add_argument('--tag', action='append', help='Repeat for AND matching across tags and labels')
        p.add_argument('--priority', type=int)
        p.add_argument('--include-archived', action='store_true')
        p.add_argument('--include-duplicates', action='store_true')
        p.add_argument('--fields', default=','.join(DEFAULT_FIELDS))
        p.add_argument('--limit', type=int, default=10)
        p.add_argument('--cursor')
    p = sub.add_parser('neighbors')
    p.add_argument('id')
    p.add_argument('--type', dest='relation_type')
    p.add_argument('--direction', default='both', choices=('incoming', 'outgoing', 'both'))
    p.add_argument('--group', choices=('administrative', 'research', 'all'))
    p.add_argument('--include-noncurrent', action='store_true')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--cursor')
    p = sub.add_parser('show')
    p.add_argument('id')
    p.add_argument('--section')
    p.add_argument('--notes', action='store_true')
    p.add_argument('--max-chars', type=int, default=3000)
    p.add_argument('--cursor')
    p = sub.add_parser('index')
    p.add_argument('action', choices=('refresh', 'rebuild'))
    sub.add_parser('validate')
    p = sub.add_parser('write')
    p.add_argument('--request-file', required=True, help='JSON request path, or - for stdin')
    p = sub.add_parser('workflow')
    flow = p.add_subparsers(dest='action', required=True)
    start = flow.add_parser('start')
    start.add_argument('--limit', type=int, default=5)
    start.add_argument('--cursor')
    start.add_argument('--tag', action='append', help='Filter candidates; global active/last sessions remain visible')
    for name in ('begin', 'checkpoint', 'end'):
        flow.add_parser(name).add_argument('--request-file', required=True)
    run = flow.add_parser('run')
    run.add_argument('run_id')
    run.add_argument('--limit', type=int, default=5)
    run.add_argument('--cursor')
    p = sub.add_parser('recover')
    p.add_argument('action', choices=('status', 'finish', 'keep-current'))
    p.add_argument('--request-file')
    try:
        args = vars(parser.parse_args(argv))
        root, project, paper = args.pop('root'), args.pop('project'), args.pop('paper')
        command = args.pop('command')
        from ticket_project import load_project, initialize, load_paper, initialize_paper
        if command == 'init':
            if not (project or paper):
                raise IndexErrorDetail('INVALID_ARGUMENT', 'init requires --project or --paper, never --root.')
            result = (initialize_paper if paper else initialize)(paper or project, args['name'], request_file(args['config_file']) if args['config_file'] else None)
            print(json.dumps(result, ensure_ascii=False, allow_nan=False))
            return 0
        config = None
        if project:
            root, config = load_project(project)
        elif paper:
            root, config = load_paper(paper)
        index = IssueIndex(root)
        if command in ('list', 'search'):
            args['fields'] = args['fields'].split(',')
            result = index.list_issues(**args)
        elif command == 'neighbors':
            result = index.neighbors(args.pop('id'), **args)
        elif command == 'show':
            result = index.get_section(args.pop('id'), **args)
        elif command == 'validate':
            result = index.validate()
        elif command == 'doctor':
            result = index.validate()
            start = IssueStore(root).workflow_start()
            result.update(project=config['project_id'] if config and not config.get('subject') else None,
                          subject=start['subject'], capsule=start['capsule'], coverage=start['coverage'], active=start['active'], source_checks=start['source_checks'])
            result.update({k: v for k, v in start.items() if k.startswith('source_check')})
        elif command == 'source':
            from issue_sources import snapshot, validate_reference
            if args['action'] == 'snapshot':
                ref = snapshot(root, args['repository'], args['path'], args['commit'], args['heading'])
                if args['object_id']:
                    ref['object_id'] = args['object_id']
                result = {'ok': True, 'source': validate_reference(ref), 'verification': 'Local source bytes only; remote publication and mathematical truth are not asserted.'}
            else:
                result = IssueStore(root).source_check(args['id'], args['limit'], args['cursor'])
        elif command == 'write':
            result = IssueStore(root).apply(request_file(args['request_file']))
        elif command == 'workflow':
            action = args.pop('action')
            store = IssueStore(root)
            if action == 'start':
                result = store.workflow_start(**args)
            elif action == 'run':
                result = store.workflow_run(**args)
            else:
                packet = request_file(args['request_file'])
                if not isinstance(packet, dict) or not isinstance(packet.get('operations'), list) or not packet['operations'] or not isinstance(packet['operations'][-1], dict) or packet['operations'][-1].get('op') != action:
                    raise IndexErrorDetail('INVALID_ARGUMENT', 'Request must end with the selected workflow operation.')
                result = store.apply(packet)
        elif command == 'recover':
            packet = request_file(args['request_file']) if args['request_file'] else {}
            if not isinstance(packet, dict) or set(packet) - {'expected_journal', 'expected_files'}:
                raise IndexErrorDetail('INVALID_ARGUMENT', 'Recovery accepts only reviewed journal/file hashes.')
            result = IssueStore(root).recover(args['action'], **packet)
        else:
            data = index.refresh(force=args['action'] == 'rebuild')
            result = {'ok': True, 'generation': data['generation'], 'issues': len(data['records']),
                      'relations': len(data['relations']), 'cache': '.cache/issues-index.json', 'stats': index.last_stats}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except IndexErrorDetail as e:
        print(json.dumps({'ok': False, 'error': {'code': e.code, 'message': str(e), 'details': e.details}}, ensure_ascii=False))
        return 2
    except OSError as e:
        print(json.dumps({'ok': False, 'error': {'code': 'FILESYSTEM_ERROR', 'message': 'Cannot access project data/cache.', 'errno': e.errno}}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
