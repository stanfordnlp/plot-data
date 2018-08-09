import argparse
import collections
import json
import csv
import random
import sys

RANDOM_SEED = 0
TRAIN_FRAC = 0.8

class QueryLine(object):
    def __init__(self, line):
        self.json = json.loads(line)
        self.session_id = self.json['sessionId']

    def utterance(self):
        if (self.is_accept()):
            return self.json['q'][1]['utterance']
        raise Exception('no utterance available')

    def query_type(self):
        return self.json['q'][0]

    def inner(self):
        return self.json['q']

    def is_accept(self):
        return self.json['q'][0]=='accept'

    def is_log(self):
        return self.json['q'][0]=='log'


def parse_args():
    parser = argparse.ArgumentParser('Process data.')
    parser.add_argument('input')
    parser.add_argument('--output', type=str, default='filtered_output.jsonl')
    parser.add_argument('--spammers', type=str, default='mturk/spammers.csv')
    parser.add_argument('--max-accepts', type=int, default=8,
                    help='filter out spammy sessions with too many lines')
    parser.add_argument('--min-accepts', type=int, default=4,
                    help='minimum number of accepts')
    parser.add_argument('--verbose', type=int, default=1)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()

# simple rules to filter out spam
def spam_filter(session_lines):
    isspam = False
    session_accepts = [l for l in session_lines if l.is_accept()]
    session_logs = [l for l in session_lines if l.is_log()]
    session_utts = set()
    for line in session_accepts:
        session_utts.add(line.utterance())

    if (len(session_utts) > OPTS.max_accepts or len(session_utts) < OPTS.min_accepts):
        isspam = True
        if OPTS.verbose > 0:
            print('rejected accepts all: %d\t distinct %d' % (len(session_accepts), len(session_utts)))
            if OPTS.verbose > 1:
                for l in session_accepts:
                    print(l.utterance())

    if (len(session_logs) > 20):
        isspam = True
        if OPTS.verbose > 0:
            print('rejected logs')

    return isspam

def process_queries():
    session_to_lines = collections.defaultdict(list)
    processed = []
    spammers = open(OPTS.spammers).readlines()
    print('spammers', spammers)
    with open(OPTS.input) as f:
        for line in f:
            queryline = QueryLine(line.strip())
            session_to_lines[queryline.session_id].append(queryline)
    for session, lines in session_to_lines.items():
        if any(l.strip() in session for l in spammers):
            print('spammer match', session)
            continue
        if spam_filter(lines):
            print('rejected: ', session)
        else:
            processed += lines

    with open(OPTS.output, 'w') as f:
        for line in processed:
            f.write(json.dumps(line.json) + '\n')

def main():
    process_queries()

if __name__ == '__main__':
    OPTS = parse_args()
    main()
