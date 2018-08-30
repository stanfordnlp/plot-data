"""
Takes the speaker querylog, produce an accept and reject list and filtered data
just performs enough filtering so that the result can be used for the listener task
"""
from query_line import QueryLine
import argparse
import collections
import json
import sys
import os

def parse_args():
    parser = argparse.ArgumentParser('Process data.')
    parser.add_argument('speaker')
    parser.add_argument('listener')
    parser.add_argument('--data-out', type=str, default='listener.jsonl')
    parser.add_argument('--status-out', type=str, default='listener.status')
    parser.add_argument('--agg-out', type=str, default='listener.aggregate')

    script_dir = os.path.abspath(os.path.dirname(__file__))
    parser.add_argument('--spammers', type=str, default=os.path.join(script_dir, 'id_spammer.txt'))
    parser.add_argument('--qualify', type=str, default=os.path.join(script_dir, 'id_qualify.txt'))
    parser.add_argument('--verbose', type=int, default=1)
    parser.add_argument('--min-verify', type=int, default=5)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def process_verify(examples, listener_log):
    verify_lines = [q for q in listener_log if q.is_verify()]
    print('number of verify', len(verify_lines))
    by_example = collections.defaultdict(lambda: {'verify':[], 'ex': None})
    for l in examples:
        assert l.is_example()
        key = l.json['queryId']
        by_example[key]['ex'] = l

    for l in verify_lines:
        assert l.is_verify()
        key = l.example_key()
        print(key)
        if by_example[key]['ex'] is None:
            print('verified something not in examples: ', l.utterance())
        by_example[key]['verify'].append(l)

    for _, v in by_example.items():
        example = v['ex']
        if example is None:
            continue
        verified = v['verify']
        example.num_verify_attempted = len(verified)
        example.num_verified = len([v for v in verified if v.example()['targetFormula']=='correct'])


def add_stats(workers):
    for _, v in workers.items():
        v['acc'] = v['verified'] / v['attempted']
        v['num_ass'] = len(v['assignments'])


def aggregate_turker(examples, verifies):
    speakers = collections.defaultdict(lambda: {'acc': 0, 'verified': 0, 'attempted': 0, 'assignments': set()})
    for l in examples:
        key = l.worker_id()
        speakers[key]['verified'] += l.num_verified
        speakers[key]['attempted'] += l.num_verify_attempted
        speakers[key]['assignments'].add(l.assignment_id())
    add_stats(speakers)

    listeners = collections.defaultdict(lambda: {'acc': 0, 'verified': 0, 'attempted': 0, 'assignments': set()})
    for l in verifies:
        key = l.worker_id()
        listeners[key]['verified'] += 1 if l.example()['targetFormula']=='correct' else 0
        listeners[key]['attempted'] += 1
        listeners[key]['assignments'].add(l.assignment_id())
    add_stats(listeners)

    speakers = sorted(speakers.items(), key=lambda x: x[1]['acc'])
    listeners = sorted(listeners.items(), key=lambda x: x[1]['acc'])

    return speakers, listeners


def write_status(all_lines):
    session_to_lines = collections.defaultdict(list)
    spammers = open(OPTS.spammers).readlines()
    for queryline in all_lines:
        session_to_lines[queryline.session_id].append(queryline)

    statuses = []
    for session, lines in session_to_lines.items():
        examples = [l for l in lines if l.is_verify()]
        if (len(examples) == 0):
            continue
        header = {'WorkerId': examples[0].worker_id(), 'AssignmentId': examples[0].assignment_id(), 'type': 'pick'}

        if any(l.strip() in session for l in spammers):
            statuses.append({**header, 'accept': False, 'reasons': ['spammer list']})
            continue

        if len(examples) < OPTS.min_verify:
            statuses.append({**header, 'accept': False, 'reasons': ['accepts < min_verify', len(examples), OPTS.min_verify]})

        statuses.append({**header, 'accept': True, 'reasons': ['default']})
    open(OPTS.status_out, 'w').write(json.dumps(statuses))


def main():
    print(OPTS.speaker, OPTS.listener)

    processed = [QueryLine(line.strip()) for line in open(OPTS.speaker, 'r').readlines()]
    listener_log = [QueryLine(line.strip()) for line in open(OPTS.listener, 'r').readlines()]
    write_status(listener_log)
    # adds annotations
    process_verify(processed, listener_log)
    # speakers, listeners = aggregate_turker(processed, listener_log)
    #
    # with open('talk.jsonl', 'w') as f:
    #     for line in processed:
    #         f.write(json.dumps(line.json_verified()) + '\n')

if __name__ == '__main__':
    OPTS = parse_args()
    main()
