"""
Takes the HITs.txt file that has a list of HITIds, and fetch assignments, workers, and submissions
code
"""

import argparse
import collections
import json
import os
import sys
import mturk_utils as m
import boto3
import datetime
import re
import base64

def parse_args():
    parser = argparse.ArgumentParser('Create mturk jobs')
    parser.add_argument('--is-sandbox', action='store_true', default=False)
    parser.add_argument('--hits', type=str, default='HITs.txt')
    parser.add_argument('--assignments', type=str, default='assignments.json')
    return parser.parse_args()


def get_code(answer):
    pattern = '<Answer><QuestionIdentifier>code</QuestionIdentifier><FreeText>(.+?)</FreeText></Answer>'
    try:
        code = re.search(pattern, answer).group(1)
    except AttributeError:
        print('code not found')
        code = ''
    return code


def check_code(sessionId, code):
    code += "=" * ((4 - len(code) % 4) % 4)
    d = base64.b64decode(code).decode('utf-8')
    obj = json.loads(d)
    return obj['sessionId'] == sessionId and obj['count'] >= 5


def main():
    is_sandbox = OPTS.is_sandbox
    client = m.get_mturk_client(is_sandbox=is_sandbox)
    print('balance', client.get_account_balance()['AvailableBalance'])

    hits = open(OPTS.hits, 'r').readlines()
    assignments = []
    for h in hits:
        response = client.list_assignments_for_hit(HITId=h.strip('\n'), MaxResults=100)
        assignments += response['Assignments']

    for a in assignments:
        print(a['WorkerId'])
        code = get_code(a['Answer'])
        print(check_code(a['WorkerId'] + '_' + a['AssignmentId'], code))


if __name__ == '__main__':
    OPTS = parse_args()
    main()
