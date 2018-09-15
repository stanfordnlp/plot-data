"""
Takes a list of hits, and convert the querylogs to downstream friendly data by

* filter junk data
* minimize by removing logging information only useful for analyzing data, which can always be recovered using the queryId
* point to context and listener id
"""
# from .query_line import QueryLine
import argparse
import collections
import json
import sys
import os
import hashlib
import jsonpatch
# import query_line.QueryLine as QueryLine
if __name__ == '__main__':
    from query_line import QueryLine
else:
    from .query_line import QueryLine

default_hits = [
'2018-08-10_00-00-00', # 0 older scheme, but could also include
# '2018-08-29_11_32_44', short trial run
'2018-08-29_22-54-16', #2
'2018-09-05_21-38-43',
'2018-09-07_11-34-48',
'2018-09-08_09-41-18',
'2018-09-09_10-28-14', #6
'2018-09-10_10-36-44', #7
'2018-09-11_11-09-18',
#'2018-09-12_11-04-34',
'2018-09-13_12-06-31',
]

def parse_args():
    parser = argparse.ArgumentParser('finalize the data for models')
    parser.add_argument('--hits', nargs='+', help='<Required> list of hit time stamps to process', default=default_hits)
    script_dir = os.path.abspath(os.path.dirname(__file__))
    parser.add_argument('--outdir', type=str, default='data')
    # parser.add_argument('--filter', type=boolean, default=True)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


def is_skip(q):
    return q.is_log() and q.log()['type'] == 'skip'


def lineinfo(line):
    if is_skip(line):
        return {
            'workerId': line.worker_id(),
            'queryId': line.query_id(),
            'type': 'skip'
        }
    elif line.is_pick():
        ex = line.example()
        t = ex['targetFormula']
        assert t == 'correct' or t == 'wrong'
        return {
            'workerId': line.worker_id(),
            'queryId': line.query_id(),
            'type': t
        }
    raise Exception('line type not allowed')


def key_from_pick(l):
    assert l.is_pick()
    example = l.example()
    if 'id' in example and example['id'] != '':
        return example['id']
    else:
        raise Exception('example does not have id')

def example_key(l):
    if l.is_pick():
        return key_from_pick(l)
    elif is_skip(l):
        return l.log()['exampleId']
    else:
        raise Exception('no id' + str(l))

def process_listener(examples, listener_log):
    by_example = collections.defaultdict(lambda: {'verify':[], 'ex': None})
    for l in examples:
        assert l.is_example()
        key = l.json['queryId']
        by_example[key]['ex'] = l

    pick_or_skip = [q for q in listener_log if q.is_pick() or is_skip(q)]
    print('number of listener pick_or_skip', len(pick_or_skip))
    for l in pick_or_skip:
        key = example_key(l)
        ex = by_example[key]['ex']  # find the speaker example
        if ex is None:
            if l.is_pick():
                print('verify not in examples: ', key, l.utterance())
            continue
        ex.listeners.append(lineinfo(l))


def aggregate_type(infolist, defaultkeys=['correct', 'wrong', 'skip']):
    counter = collections.Counter(map(lambda i: i['type'], infolist))
    return {k: counter[k] for k in defaultkeys}

def json_patch(context, targetValue):
    diff = jsonpatch.JsonPatch.from_diff(context, targetValue, optimization=False)
    return json.loads(diff.to_string())

def canonical(context, targetValue):
    diff = json_patch(context, targetValue)
    assert len(diff) == 1, 'diff not simple, no canonical'
    diff = diff[0]
    op = diff['op']
    assert op == 'replace' or op == 'add', 'not replace or add'
    # p should not include trailing /
    def strip(p, v):
        # print(type(v))
        if isinstance(v, dict):
            assert len(v.keys()) == 1, 'must be simple object: ' + str(diff)
            k = list(v.keys())[0]
            return strip(p + '/' + k, v[k])
        else:
            return p, v
    ps, vs = strip(diff['path'], diff['value'])
    return ps[1:].replace('/', ' ') +  ': ' + json.dumps(vs).strip('"')


class Contexts(object):
    def __init__(self):
        self.contexts = {}

    def hash(self, obj):
        seed = json.dumps(obj, sort_keys=True)
        return hashlib.md5(seed.encode('utf-8')).hexdigest()[0:7]

    def add(self, inner):
    # add context and checks that data schema is consistent, returns id
        spec = inner['context']
        schema = inner['schema']
        datasetURL = inner['datasetURL']
        id = self.hash(spec)
        if id not in self.contexts:
            self.contexts[id] = {'context': spec, 'schema': schema, 'datasetURL': datasetURL}
        else:
            old = self.contexts[id]
            try:
                assert json.dumps(spec) == json.dumps(old['context'])
                # assert datasetURL == old['datasetURL']
                # assert self.hash(schema) == self.hash(old['schema'])
            except AssertionError as e:
                # print(inner)
                diff = json_patch(spec, inner['targetValue'])
                print('assertion error', inner['utterance'], diff)
        return id

    def dumps(self):
        return json.dumps([ {k: v['context']} for k,v in self.contexts.items()], sort_keys=True)

def finalize(hits, outdir):
    slines = []
    llines = []
    for h in hits:
        print('reading', h)
        speaker_path = os.path.join('hits', h, 'speaker.jsonl')
        listener_path = os.path.join('hits', h, 'listener.raw.jsonl')
        slines += [l for l in open(speaker_path, 'r').readlines()]
        llines += [l for l in open(listener_path, 'r').readlines()]

    examples = map(lambda l: QueryLine(l), slines)
    examples = [ex for ex in examples if ex.is_example()]
    listener_log = map(lambda l: QueryLine(l), llines)

    # adds annotations
    process_listener(examples, listener_log)
    # filtered = filter_desynced(examples)
    contexts = Contexts()

    with open(os.path.join(outdir, 'examples.jsonl'), 'w')  as examplef, open(os.path.join(outdir, 'query.jsonl'), 'w') as queryf:
        for l in examples:
            cid = contexts.add(l.inner()[1])
            context = l.example()['context']
            targetFormula = l.example()['targetFormula']
            targetValue = l.example()['targetValue']
            patch = json_patch(context, targetValue)

            if len(patch) != 1:
                print('desyned')
                continue
            print(targetFormula, patch)

            cf = canonical(context, targetValue)
            if not (targetFormula == cf or targetFormula == cf + '.0' or targetFormula.startswith('set')):
                print('{}\n{}'.format(targetFormula, cf))
                continue

            if len(l.utterance()) < 3:
                print('still too short', l.utterance())
                continue


            jsonl = {**l.json,
                'listeners': l.listeners,
            }

            queryf.write(json.dumps(jsonl) + '\n')

            jsonl = {
                'queryId': l.query_id(),
                'utterance': l.utterance(),
                'patch': patch,
                'targetFormula': cf,
                'contextId': cid,
                'listeners': l.listeners,
            }
            # print(jsonl)
            examplef.write(json.dumps(jsonl) + '\n')

    with open(os.path.join(outdir, 'context.json'), 'w')  as f:
        f.write(contexts.dumps())

if __name__ == '__main__':
    OPTS = parse_args()
    finalize(OPTS.hits, OPTS.outdir)
