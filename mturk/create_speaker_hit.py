import argparse
import collections
import json
import sys
import mturk_utils as m
import boto3
import functools

def parse_args():
    parser = argparse.ArgumentParser('Create mturk jobs')
    parser.add_argument('--is-sandbox', action='store_true', default=False)
    parser.add_argument('--num-hit', type=int, default=1)
    parser.add_argument('--num-assignment', type=int, default=5)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


def main():
    is_sandbox = OPTS.is_sandbox
    client = m.get_mturk_client(is_sandbox=is_sandbox)
    print('balance', client.get_account_balance()['AvailableBalance'])

    # The question we ask the workers is contained in this file.
    xml_template = open("mturk/amt.xml", "r").read()
    content = open("mturk/speaker.html", "r").read()
    question = xml_template.format(content)

    environments = {
        "live": {
            "endpoint": "https://mturk-requester.us-east-1.amazonaws.com",
            "preview": "https://www.mturk.com/mturk/preview",
            "manage": "https://requester.mturk.com/mturk/manageHITs",
            "reward": "0.25"
        },
        "sandbox": {
            "endpoint": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
            "preview": "https://workersandbox.mturk.com/mturk/preview",
            "manage": "https://requestersandbox.mturk.com/mturk/manageHITs",
            "reward": "0.25"
        },
    }
    mturk_environment = environments["live"] if not is_sandbox else environments["sandbox"]

    print('about to submit {} assignments for a total payout of ${}'.format(OPTS.num_hit*OPTS.num_assignment, OPTS.num_hit*OPTS.num_assignment*float(mturk_environment["reward"])*2.2))
    # Example of using qualification to restrict responses to Workers who have had
    # at least 80% of their assignments approved. See:
    # http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
    worker_requirements = [{
        'QualificationTypeId': '000000000000000000L0',
        'Comparator': 'GreaterThanOrEqualTo',
        'IntegerValues': [95],
        'RequiredToPreview': True,
    }, {
        'QualificationTypeId': '00000000000000000040',
        'Comparator': 'GreaterThanOrEqualTo',
        'IntegerValues': [10],
        'RequiredToPreview': True,
    }, {
        'QualificationTypeId': '00000000000000000071',
        'Comparator': 'In',
        'LocaleValues': [
            {'Country': 'US'},
            {'Country': 'CA'},
            {'Country': 'GB'},
            {'Country': 'AU'},
            {'Country': 'NZ'}
        ],
        'RequiredToPreview': True
    }]

    # print(question)
    # Create the HIT
    for i in range(OPTS.num_hit):
        response = client.create_hit(
            MaxAssignments=OPTS.num_assignment,
            AutoApprovalDelayInSeconds=3*24*3600,
            LifetimeInSeconds=2*24*3600,
            AssignmentDurationInSeconds=1800,
            Title='write a command for producing the new plot',
            Keywords='percy plotting nlp language graph label text ml nlp data vlspeaker',
            Description='give a command for producing the new plot based on the old one',
            Reward=mturk_environment['reward'],
            Question=question,
            QualificationRequirements=worker_requirements if not is_sandbox else [],
        )

        # The response included several fields that will be helpful later
        hit_type_id = response['HIT']['HITTypeId']
        hit_id = response['HIT']['HITId']
        print("\nCreated HIT {}: {}".format(i, hit_id))

        print("\nYou can work the HIT here:")
        print(mturk_environment['preview'] + "?groupId={}".format(hit_type_id))


if __name__ == '__main__':
    OPTS = parse_args()
    main()
