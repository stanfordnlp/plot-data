import mturk_utils as m
import boto3
import json, csv

is_sandbox = False
qualification_name = 'plot-diff'
description = 'reasonable turkers who succeeded in both generation and differences'

client = m.get_mturk_client(is_sandbox=is_sandbox)
qual_id = m.find_or_create_qualification(qualification_name, description, is_sandbox)
print(qual_id)
m.give_worker_qualification('AM2KK02JXXW48', qual_id, value=1, is_sandbox=is_sandbox)
# This will return $10,000.00 in the MTurk Developer Sandbox
print(client.get_account_balance()['AvailableBalance'])

with open('./bannedturkers.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        turkerid = row[0]
        print('banning turker: ' + turkerid)
        client.create_worker_block(WorkerId=turkerid, Reason='spamming on plot-diff')

response = client.list_worker_blocks()
print(json.dumps(response))
