import json


# lightweight wrapper around each queryline
class QueryLine(object):
    def __init__(self, line):
        try:
            self.json = json.loads(line)
        except Exception as ex:
            print(ex, line)
        self.session_id = self.json['sessionId']
        self.num_verified = 0
        self.num_verify_attempted = 0

    def json_verified(self):
        self.json['num_verified'] = self.num_verified
        self.json['num_verify_attempted'] = self.num_verify_attempted
        return self.json

    def utterance(self):
        if (self.is_accept()):
            return self.json['q'][1]['utterance']
        raise Exception('no utterance available')

    def query_type(self):
        return self.json['q'][0]

    def inner(self):
        return self.json['q']

    def is_accept(self):
        return self.json['q'][0]=='accept'

    def is_example(self):
        return self.json['q'][0]=='accept' and self.json['q'][1]['type']=='label'

    def is_verify(self):
        return self.json['q'][0]=='accept' and self.json['q'][1]['type']=='pick'

    def worker_id(self):
        id = self.session_id
        if id.startswith('A') and '_' in id:
            return id.split('_')[0]
        return self.session_id

    def assignment_id(self):
        id = self.session_id
        if id.startswith('A') and '_' in id:
            return id.split('_')[1]
        return self.session_id

    def is_log(self):
        return self.json['q'][0]=='log'

    def example(self):
        return self.json['q'][1]

    def example_key(self):
        context = self.example()['context']
        utt = self.utterance()
        return hash(utt + json.dumps(context, sort_keys=True))

    def __repr__(self):
        return self.utterance()
