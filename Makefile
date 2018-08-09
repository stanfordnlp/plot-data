PROC_DIR=processed_querylog

all : filter

filter:
	mkdir -p $(PROC_DIR)
	for name in turk20180808 turk20180805 turk20180803; do \
		python process_queries.py querylog/$$name.jsonl  --verbose 2 --max-accepts 10 --spammers mturk/id_spammer.txt --output $(PROC_DIR)/$$name.f.json; \
	done
