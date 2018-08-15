PROC_DIR=output

all : filter

filter:
	mkdir -p $(PROC_DIR)
	for name in turk20180810 turk20180808 turk20180805 turk20180803; do \
		python process_queries.py querylog/$$name.jsonl  --verbose 2 --max-accepts 10 \
		--spammers mturk/id_spammer.txt --qualify mturk/id_qualify.txt \
		--output $(PROC_DIR)/$$name.f.json --status-output $(PROC_DIR)/$$name.status.json; \
	done
