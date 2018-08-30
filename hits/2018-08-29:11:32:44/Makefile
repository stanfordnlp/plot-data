MT_PATH=../../mturk
SPEAKER_EXEC=2
LISTENER_EXEC=6
.PHONY: clean s-clean l-clean all

speaker.raw.jsonl:
	wget -O $@ http://jonsson.stanford.edu:8405/execs/$(SPEAKER_EXEC).exec/query.jsonl

speaker.jsonl speaker.status: speaker.raw.jsonl
	python $(MT_PATH)/process_speaker.py $<

speaker.assignments: speaker.HITs.txt
	python $(MT_PATH)/hits_to_assignments.py --hits $< --assignments $@

speaker.review: speaker.assignments speaker.status
	python $(MT_PATH)/review.py --status $(word 2,$^) --assignments $< --review-out $@

listener.raw.jsonl:
	wget -O $@ http://jonsson.stanford.edu:8405/execs/$(LISTENER_EXEC).exec/query.jsonl

listener.aggregate speaker.aggregate listener.status: speaker.jsonl listener.raw.jsonl
	python $(MT_PATH)/process_listener.py $^

listener.assignments: listener.HITs.txt
	python $(MT_PATH)/hits_to_assignments.py --hits $< --assignments $@

listener.review: listener.assignments listener.status
	python $(MT_PATH)/review.py --status $(word 2,$^) --assignments $<

verified.json: speaker.jsonl listener.jsonl

visualize: speaker.visualize listener.visualize

speaker.visualize: speaker.aggregate
	python $(MT_PATH)/visualize.py --input $< --output speaker.html --with-utterances

listener.visualize: listener.aggregate
	python $(MT_PATH)/visualize.py --input $< --output listener.html

clean-speaker:
	rm speaker.jsonl speaker.status speaker.aggregate
	rm speaker.assignments

clean: s-clean l-clean
