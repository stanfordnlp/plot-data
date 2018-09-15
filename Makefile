all: data
	python mturk/finalize_data.py --outdir data

data:
	mkdir -p data

gh-pages:
	gh-pages -d data
