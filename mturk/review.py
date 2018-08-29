"""
Goes through assignments and queries the status for reviews
"""

import argparse
import collections
import json
import sys
import mturk_utils as m
import boto3
import functools

def parse_args():
    parser = argparse.ArgumentParser('Reject mturk jobs')
    parser.add_argument('--assignments', type=str, default='speaker.assignments.json')
    parser.add_argument('--status', type=str, default='speaker.status.json')
    parser.add_argument('--reviewed-status', type=str, default='speaker.assignments.reviewed.json')
    parser.add_argument('--is-sandbox', action='store_true', default=False)
    return parser.parse_args()

def main():
    is_sandbox = OPTS.is_sandbox
    client = m.get_mturk_client(is_sandbox=is_sandbox)
    print(client.get_account_balance()['AvailableBalance'])
    by_worker = collections.defaultdict(lambda: {'accepted': 0, 'rejected': 0})

    assignments = json.loads(open(OPTS.assignments, 'r').read())
    statuses = json.loads(open(OPTS.status, 'r').read())
    status_dict = {(s['WorkerId'], s['AssignmentId']): s for s in statuses}
    for s in assignments:
        worker_id, assignment_id = s['WorkerId'], s['AssignmentId']
        try:
            response = client.get_assignment(AssignmentId=assignment_id)
            prev_status = response['Assignment']['AssignmentStatus']
            s['prev_status'] = prev_status
            accept = status_dict[(worker_id, assignment_id)]['accept']
            if accept is False:
                by_worker[worker_id]['rejected'] += 1
                response = client.reject_assignment(
                    AssignmentId=assignment_id,
                    RequesterFeedback='thanks for trying our task, but your assignment has been rejected.'
                )
                s['next_status'] = 'Rejected'
            else:
                by_worker[worker_id]['accepted'] += 1
                response = client.approve_assignment(
                    AssignmentId=assignment_id,
                    RequesterFeedback='thanks for trying our task, your assignment has been approved.',
                    OverrideRejection=True
                )
                s['next_status'] = 'Accepted'
        except KeyError as e:
            s['error_msg'] = str(e)
        except client.exceptions.RequestError as e:
            s['error_msg'] = str(e)

        print(s)

    with open(OPTS.reviewed_status, 'w') as f:
        f.writelines(json.dumps(assignments))
    print(by_worker)

if __name__ == '__main__':
    OPTS = parse_args()
    main()
