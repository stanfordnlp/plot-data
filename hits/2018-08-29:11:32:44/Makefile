MT_PATH=../../mturk/
SPEAKER_EXEC=2
LISTENER_EXEC=6

speaker.jsonl:
	wget -O speaker.jsonl http://jonsson.stanford.edu:8405/execs/$(SPEAKER_EXEC).exec/query.jsonl

speaker speaker.f.jsonl speaker.status.json speaker.aggregate.json: speaker.jsonl
	python $(MT_PATH)filter_speaker_querylog.py speaker.jsonl

speaker.assignments_from_hit.json: HITs.txt
	python $(MT_PATH)hits_to_assignments.py --hits HITs.txt --assignments speaker.assignments_from_hit.json

review: speaker.assignments.reviewed.json
	jq . speaker.assignments.reviewed.json

speaker.assignments.reviewed.json: speaker.assignments_from_hit.json speaker.status.json
	python $(MT_PATH)review.py --status speaker.status.json --assignments speaker.assignments_from_hit.json

listener.jsonl:
	wget -O listener.jsonl http://jonsson.stanford.edu:8405/execs/$(LISTENER_EXEC).exec/query.jsonl

verified.json: speaker.f.jsonl listener.jsonl

clean:
	rm speaker.f.jsonl speaker.status.json speaker.aggregate.json
	rm speaker.assignments_from_hit.json
	rm verified.json
