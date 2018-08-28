PROC_DIR=output

all : verify20180810 turk20180810 turk20180808 turk20180805 turk20180803

verify20180810 turk20180810 turk20180808 turk20180805 turk20180803: outputdir
	python process_queries.py querylog/$@.jsonl  --verbose 2 --max-accepts 10 \
	--spammers mturk/id_spammer.txt --qualify mturk/id_qualify.txt \
	--output-dir $(PROC_DIR)/$@/; \

gh-pages:
	gh-pages -d output

outputdir:
	mkdir -p $(PROC_DIR)
