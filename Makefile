all: data
	python mturk/finalize.py

data:
	mkdir -p data

gh-pages:
	gh-pages -d data
