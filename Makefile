PROC_DIR=output
FULL=speaker.listener.jsonl
MIN=speaker.listener.min.jsonl
all: data
	cat hits/2018-08-10_00-00-00/$(FULL) hits/2018-08-29_22-54-16/$(FULL) > data/full.jsonl
	cat hits/2018-08-10_00-00-00/$(MIN)  hits/2018-08-29_22-54-16/$(MIN) > data/min.jsonl

data:
	mkdir -p data

gh-pages:
	gh-pages -d data
