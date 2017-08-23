from jsondiff import diff 
import json
numLabels = 0
numRephrase = 0
for line in open("response.jsonl", "r"):
    linedict = json.loads(line) 
    query = json.loads(linedict['q'])
    #constraints - MODIFY THIS depending on logs
    if(query[0]=="accept" and "2017-08" in linedict['time']):
        if 'type' in query[1].keys() and query[1]['type'] == "label":
            numLabels += 1
            if(query[1]['utterance'] != query[1]['issuedQuery']):
                numRephrase += 1 
                #check to make sure formula not included and if difference between two plots 
                if "$" not in query[1]['utterance'] and bool(diff(query[1]['context'], query[1]['targetValue'])) == True:
                    construct_dict = {}
                    construct_dict["utterance"] = query[1]['utterance']
                    construct_dict["targetFormula"] = diff(query[1]['context'],query[1]['targetValue'])
                    construct_dict["context"] = query[1]['context']
                    construct_dict["targetValue"] = query[1]['targetValue'] 
                    u_d = json.dumps(construct_dict)
                    print(u_d)                    
print("Number of Labels: "+str(numLabels))
print("Number of Rephrases: "+str(numRephrase))             
