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
    parser.add_argument('--output', type=str, default='status.out.jsonl')
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
    by_worker = collections.defaultdict(lambda: {'accepted': 0, 'rejected': 0})

    with open(OPTS.input, 'r') as f:
        statuses = json.loads(f.read())
        for s in statuses:
            worker_id, assignment_id = s['workerId'], s['assignmentId']
            try:
                response = client.get_assignment(AssignmentId=assignment_id)
                prev_status = response['Assignment']['AssignmentStatus']
                s['prev_status'] = prev_status
                if s['accept'] is False:
                    by_worker[worker_id]['rejected'] += 1
                    response = client.reject_assignment(
                        AssignmentId=assignment_id,
                        RequesterFeedback='thanks for trying our task, but your assignment has been rejected.'
                    )
                    s['next_status'] = 'Rejected'
                elif s['accept'] == True:
                    by_worker[worker_id]['accepted'] += 1
                    response = client.approve_assignment(
                        AssignmentId=assignment_id,
                        RequesterFeedback='thanks for trying our task, your assignment has been approved.',
                        OverrideRejection=False
                    )
                    s['next_status'] = 'Accepted'
            except Exception as e:
                s['error_msg'] = e
            print(s)

        with open(OPTS.output, 'w') as f:
            f.writelines(statuses)
    # This will return $10,000.00 in the MTurk Developer Sandbox
    # response = client.list_worker_blocks()
    print(by_worker)

if __name__ == '__main__':
    OPTS = parse_args()
    main()
