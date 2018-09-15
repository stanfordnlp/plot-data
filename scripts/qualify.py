import argparse
import collections
import json
import sys
import mturk_utils as m
import boto3
import functools

def parse_args():
    parser = argparse.ArgumentParser('Reward and bonus')
    parser.add_argument('input', type=str, default='output/')
    parser.add_argument('--output', type=str, default='record.json')
    parser.add_argument('--reason', type=str, default='speaker')
    parser.add_argument('--is-sandbox', action='store_true', default=False)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


def main():
    is_sandbox = OPTS.is_sandbox
    client = m.get_mturk_client(is_sandbox=is_sandbox)
    print(client.get_account_balance()['AvailableBalance'])

    with open(OPTS.input, 'r') as f:
        workers = json.loads(f.read())
        for w in workers:
            worker_id = w[0]
            assignments = w[1]['assignments']
            acc = w[1]['acc']
            attempted = w[1]['attempted']
            try:
                if attempted > 200 and acc > 0.8:
                    w[1]['bonus'] = True
                    response = client.send_bonus(
                        WorkerId=worker_id,
                        BonusAmount='2.50',
                        AssignmentId=assignments[0],
                        Reason='On our plotting task, you achieved a high accuracy of %d, here is a bonus.' % acc,
                        UniqueRequestToken=assignments[0] + OPTS.reason
                    )
                    print(response)
            except Exception as e:
                w[1]['error'] = str(e)
                print(e)

        print('number bonuses: %d' % len(list(l for l in workers if 'bonus' in l[1])))
        with open(OPTS.output, 'w') as f:
            json.dump(workers, f)

if __name__ == '__main__':
    OPTS = parse_args()
    main()
