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
            "reward": "0.00"
        },
        "sandbox": {
            "endpoint": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
            "preview": "https://workersandbox.mturk.com/mturk/preview",
            "manage": "https://requestersandbox.mturk.com/mturk/manageHITs",
            "reward": "0.5"
        },
    }
    mturk_environment = environments["live"] if not is_sandbox else environments["sandbox"]

    # Example of using qualification to restrict responses to Workers who have had
    # at least 80% of their assignments approved. See:
    # http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
    worker_requirements = [{
        'QualificationTypeId': '000000000000000000L0',
        'Comparator': 'GreaterThanOrEqualTo',
        'IntegerValues': [90],
        'RequiredToPreview': True,
    }, {
        'QualificationTypeId': '00000000000000000040',
        'Comparator': 'GreaterThanOrEqualTo',
        'IntegerValues': [10],
        'RequiredToPreview': True,
    }]

    print(question)
    # Create the HIT
    response = client.create_hit(
        MaxAssignments=5,
        AutoApprovalDelayInSeconds=3*24*3600,
        LifetimeInSeconds=2*24*3600,
        AssignmentDurationInSeconds=1800,
        Title='write a command to produce the new plot',
        Keywords='percy plotting nlp language graph label text ml nlp data visualization',
        Description='give a command for producing the new plot based on the old one',
        Reward=mturk_environment['reward'],
        Question=question,
        QualificationRequirements=worker_requirements,
    )

    # The response included several fields that will be helpful later
    hit_type_id = response['HIT']['HITTypeId']
    hit_id = response['HIT']['HITId']
    print("\nCreated HIT: {}".format(hit_id))

    print("\nYou can work the HIT here:")
    print(mturk_environment['preview'] + "?groupId={}".format(hit_type_id))

    print("\nAnd see results here:")
    print(mturk_environment['manage'])


if __name__ == '__main__':
    OPTS = parse_args()
    main()
