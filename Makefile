all: data/query.jsonl data/plot-data.jsonl data/stats.json
	jq . data/stats.json

data/stats.json: data/query.jsonl
	python scripts/stats.py --query $< --out $@

data/query.jsonl data/plot-data.jsonl: data
	python scripts/finalize_data.py --outdir data

data:
	mkdir -p data


upload: data
	# npm install -g gh-pages
	gh-pages --dist data --branch data

clean:
	rm -rf data
