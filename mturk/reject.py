import argparse
import collections
import json
import sys
import mturk_utils as m
import boto3

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
    rejected_current = 0
    rejected_status = 0

    with open(OPTS.input, 'r') as f:
        statuses = json.loads(f.read())
        for s in statuses:
            print(s)
            session_id = s['sessionId']
            if '_' not in session_id or not session_id.startswith('A'):
                print('invalid sessionId')
                continue
            worker_id, assignment_id = session_id.split("_")

            if s['accept'] == False:
                response = {}
                worker_rejects[worker_id] += 1
                try:
                    response = client.get_assignment(AssignmentId=assignment_id)
                    status = response['Assignment']['AssignmentStatus']
                    print('assignment_status', response['Assignment']['AssignmentStatus'])
                    rejected_status += 1 if status=='Rejected' else 0
                    response = client.reject_assignment(
                        AssignmentId=assignment_id,
                        RequesterFeedback='Thanks for trying our task, but your assignment has been rejected for failing quality control.'
                    )
                    reject_current += 1
                    print('rejected ', worker_id, assignment_id, response)
                    if OPTS.block:
                        client.create_worker_block(WorkerId=worker_id, Reason='Low quality work on plot-diff')
                except Exception as e:
                    print(e)
                    continue
    print('rejected_current', rejected_current)
    print('rejected_status', rejected_status)


    # This will return $10,000.00 in the MTurk Developer Sandbox
    # response = client.list_worker_blocks()
    print(worker_rejects)

if __name__ == '__main__':
    OPTS = parse_args()
    main()
