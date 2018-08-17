import argparse
import collections
import json
import sys
import mturk_utils as m
import boto3
import functools

def parse_args():
    parser = argparse.ArgumentParser('Reject mturk jobs')
    parser.add_argument('input', type=str, default='status.jsonl')
    parser.add_argument('--is-sandbox', action='store_true', default=False)
    parser.add_argument('--block', type=bool, default=False)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()

def main():
    is_sandbox = OPTS.is_sandbox
    client = m.get_mturk_client(is_sandbox=is_sandbox)
    print(client.get_account_balance()['AvailableBalance'])
    worker_rejects = collections.defaultdict(int)
    prev_status = []
    next_status = []

    with open(OPTS.input, 'r') as f:
        statuses = json.loads(f.read())
        for s in statuses:
            print(s)

            worker_id, assignment_id = s['workerId'], s['assignmentId']

            try:
                response = client.get_assignment(AssignmentId=assignment_id)
                print('assignment_status', response['Assignment']['AssignmentStatus'])
                if s['accept'] == False:
                    response = {}
                    worker_rejects[worker_id] += 1
                    response = client.reject_assignment(
                        AssignmentId=assignment_id,
                        RequesterFeedback='thanks for trying our task, but your assignment has been rejected.'
                    )
                    next_status += ['rejected']
                    print('rejected ', worker_id, assignment_id, response)
                elif s['accept'] == True:
                    response = client.approve_assignment(
                        AssignmentId=assignment_id,
                        RequesterFeedback='thanks for trying our task, your assignment has been approved.',
                        OverrideRejection=False
                    )
                    next_status += ['accepted']
                    print('accepted ', worker_id, assignment_id, response)
            except Exception as e:
                print('error_message', e)
                continue

    def addkey(d, k):
        d[k]+=1
        return d
    functools.reduce(addkey, prev_status, collections.defaultdict(int))

    print('previous_status', functools.reduce(addkey, prev_status, collections.defaultdict(int)))
    print('next_status', functools.reduce(addkey, next_status, collections.defaultdict(int)))


    # This will return $10,000.00 in the MTurk Developer Sandbox
    # response = client.list_worker_blocks()
    print(worker_rejects)

if __name__ == '__main__':
    OPTS = parse_args()
    main()
