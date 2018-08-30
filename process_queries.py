import argparse
import collections
import json
import sys
import os

def parse_args():
    parser = argparse.ArgumentParser('Process data.')
    parser.add_argument('input')
    parser.add_argument('--output-dir', type=str, default='./output/')
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

# lightweight wrapper around each queryline
class QueryLine(object):
    def __init__(self, line):
        try:
            self.json = json.loads(line)
        except Exception as ex:
            print(ex, line)
        self.session_id = self.json['sessionId']
        self.num_verified = 0
        self.num_verify_attempted = 0

    def json_verified(self):
        self.json['num_verified'] = self.num_verified
        self.json['num_verify_attempted'] = self.num_verify_attempted
        return self.json

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

    def is_example(self):
        return self.json['q'][0]=='accept' and self.json['q'][1]['type']=='label'

    def is_pick(self):
        return self.json['q'][0]=='accept' and self.json['q'][1]['type']=='pick'

    def worker_id(self):
        id = self.session_id
        if id.startswith('A') and '_' in id:
            return id.split('_')[0]
        return self.session_id

    def assignment_id(self):
        id = self.session_id
        if id.startswith('A') and '_' in id:
            return id.split('_')[1]
        return self.session_id

    def is_log(self):
        return self.json['q'][0]=='log'

    def example(self):
        return self.json['q'][1]

    def example_key(self):
        context = self.example()['context']
        utt = self.utterance()
        return hash(utt + json.dumps(context, sort_keys=True))

    def __repr__(self):
        return self.utterance()

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
       if isinstance(obj, set):
          return list(obj)
       return json.JSONEncoder.default(self, obj)

# simple rules to filter out spam
def spam_filter(session_lines):
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

def process_queries(all_lines):
    session_to_lines = collections.defaultdict(list)
    processed = []
    spammers = open(OPTS.spammers).readlines()
    whitelist = open(OPTS.qualify).readlines()

    for queryline in all_lines:
        session_to_lines[queryline.session_id].append(queryline)

    statuses = []
    for session, lines in session_to_lines.items():
        examples = [l for l in lines if l.is_example()]
        if (len(examples) == 0): continue

        header = {'workerId': examples[0].worker_id(), 'assignmentId': examples[0].assignment_id(), 'type': 'label'}

        if any(l.strip() in session for l in spammers):
            statuses.append({**header, 'accept': False, 'reasons': ['spammer list']})
            continue

        reasons, info = spam_filter(lines)
        if any(l.strip() in session for l in whitelist):
            statuses.append({**header, 'accept': True, 'reasons': ['qualified'] + reasons})
            processed += examples
            continue

        if len(reasons) > 0:
            if len(info['distincts']) > 3:
                print(session, 'spam_filter', reasons, info['distincts'])
            statuses.append({**header, 'accept': False, 'reasons': reasons})
        else:
            processed += examples
            statuses.append({**header, 'accept': True, 'reasons': reasons})
    return processed, statuses

def process_verify(examples, verify_lines):
    print('number of verify', len(verify_lines))
    by_example = collections.defaultdict(lambda: {'ex': [], 'verify': []})
    for l in examples:
        if l.is_example():
            key = l.example_key()
            by_example[key]['ex'] += [l]

    worker_session = set()
    for l in verify_lines:
        assert l.is_pick()
        worker_session.add(l.session_id)
        key = l.example_key()
        if len(by_example[key]['ex']) == 0:
            print('skipping', l)
            continue
        by_example[key]['verify'] += [l]

    print('number submissions', len(worker_session))

    for _,v in by_example.items():
        example = v['ex']
        if (len(example) > 1):
            print('warning.multiple: %s' % example[0].utterance())
            continue
        if (len(example) == 0):
            continue
        example = example[0]
        verified = v['verify']
        example.num_verify_attempted = len(verified)
        example.num_verified = len([v for v in verified if v.example()['targetFormula']=='correct'])

def add_stats(workers):
    for _, v in workers.items():
        v['acc'] = v['verified'] / v['attempted']
        v['num_ass'] = len(v['assignments'])

def aggreate_turker(examples, verifies):
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

def prepdir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def main():
    dir = OPTS.output_dir
    prepdir(dir)
    all_lines = []
    with open(OPTS.input) as f:
        all_lines = [QueryLine(line.strip()) for line in f]

    examples_logs = [q for q in all_lines if q.is_example() or q.is_log()]
    processed, statuses = process_queries(examples_logs)
    with open(os.path.join(dir, 'filtered.jsonl'), 'w') as f:
        for line in processed:
            f.write(json.dumps(line.json) + '\n')

    verify_lines = [q for q in all_lines if q.is_pick()]

    if len(verify_lines) == 0:
        print('not verified')
        return

    process_verify(processed, verify_lines)
    speakers, listeners = aggreate_turker(processed, verify_lines)

    with open(os.path.join(dir, 'verified.jsonl'), 'w') as f:
        for line in processed:
            f.write(json.dumps(line.json_verified()) + '\n')

    for k, v in listeners:
        for a in v['assignments']:
            statuses.append({'workerId': k, 'assignmentId': a, 'type': 'pick', 'accept': v['acc'] > 0.5})

    with open(os.path.join(dir, 'speakers.json'), 'w') as f:
        json.dump(speakers, f, cls=SetEncoder)

    with open(os.path.join(dir, 'listeners.json'), 'w') as f:
        json.dump(listeners, f, cls=SetEncoder)

    with open(os.path.join(dir, 'status.json'), 'w') as f:
        json.dump(statuses, f)


if __name__ == '__main__':
    OPTS = parse_args()
    main()
