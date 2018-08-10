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
        try:
            self.json = json.loads(line)
        except:
            print(line)
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
    parser.add_argument('--status-output', type=str, default='status.jsonl')
    parser.add_argument('--spammers', type=str, default='mturk/id_spammer.txt')
    parser.add_argument('--qualify', type=str, default='mturk/id_qualify.txt')
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
    reasons = []
    session_accepts = [l for l in session_lines if l.is_accept()]
    session_logs = [l for l in session_lines if l.is_log()]
    session_utts = set()

    for line in session_accepts:
        session_utts.add(line.utterance())

    vocab = set()
    for s in session_utts:
        vocab.update(s.split(' '))

    # reject spam or those that are obviously not doing enough
    if (len(session_accepts) > OPTS.max_accepts or len(session_utts) < OPTS.min_accepts):
        reasons.append('%d accepts, %d distinct' % (len(session_accepts), len(session_utts)))

    # reject those that generated a lot of spammy logs
    if (len(session_logs) > 50):
        reasons.append('too many log %d' % len(session_logs))

    # reject those with lots of empties, single words and double words
    num_too_short = len([l for l in session_accepts if len(l.utterance().strip().split()) < 3])
    vocab_size = len(vocab)
    if vocab_size < 10:
        reasons.append('vocab too small: ' + str(vocab_size))
    if num_too_short > 2:
        reasons.append('too many shorts: ' + str(num_too_short))

    info = {'distincts': session_utts}
    return reasons, info


def process_queries():
    session_to_lines = collections.defaultdict(list)
    processed = []
    spammers = open(OPTS.spammers).readlines()
    whitelist = open(OPTS.qualify).readlines()

    with open(OPTS.input) as f:
        for line in f:
            queryline = QueryLine(line.strip())
            session_to_lines[queryline.session_id].append(queryline)

    statuses = []
    for session, lines in session_to_lines.items():
        examples = [l for l in lines if l.is_accept()]
        line = {'sessionId': session, 'accept': True, 'reason': []}

        if any(l.strip() in session for l in spammers):
            statuses.append({'sessionId': session, 'accept': False, 'reasons': ['spammer list']})
            continue

        reasons, info = spam_filter(lines)
        if any(l.strip() in session for l in whitelist):
            statuses.append({'sessionId': session, 'accept': True, 'reasons': ['qualified'] + reasons})
            processed += examples
            continue

        if len(reasons) > 0:
            if len(info['distincts']) > 3:
                print(session, 'spam_filter', reasons, info['distincts'])
            statuses.append({'sessionId': session, 'accept': False, 'reasons': reasons})
        else:
            processed += examples
            statuses.append({'sessionId': session, 'accept': True, 'reasons': reasons})

    with open(OPTS.output, 'w') as f:
        for line in processed:
            f.write(json.dumps(line.json) + '\n')

    with open(OPTS.status_output, 'w') as f:
        json.dump(statuses, f)

def main():
    process_queries()

if __name__ == '__main__':
    OPTS = parse_args()
    main()
