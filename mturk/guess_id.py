"""
scripts for some backwards compatibility by adding queryId with hashing
"""
import argparse
import json
import hashlib
import re
import sys
from query_line import QueryLine
import base64

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('--mode', default='speaker', help='speaker|listener, for speaker set .queryId whereas for listener set .q[1].id')
OPTS = parser.parse_args()

lines = []
with open(OPTS.input, 'r') as f:
    lines = f.readlines()

def hash_query(query):
    b = query['q'][1]
    keys = []
    seed = b['utterance']
    for k in keys:
        if k in b:
            seed += json.dumps(b[k], sort_keys=True)
    return hashlib.md5(seed.encode('utf-8')).hexdigest()
    # return base64.b64encode(bytes(number, 'utf-8')).decode('utf-8')[0:10]

for l in lines:
    jq = json.loads(l)
    if jq['q'][0] != 'accept':
        continue
    id = hash_query(jq)
    body = jq['q'][1]
    if OPTS.mode == 'speaker':
        jq['queryId'] = id
        if 'targetFormula' not in body:
            print('not targetFormula?', body, file=sys.stderr)
            continue
        old = body['targetFormula']
        print('old', old, file=sys.stderr)
        body['targetFormula'] = re.sub(r'^set ([a-zA-Z ]*) to (\S*)$', r'\1: \2', old)
    elif OPTS.mode == 'listener':
        body['id'] = id
    else:
        raise Exception('wrong mode')
    print(json.dumps(jq))
