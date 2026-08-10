.PHONY: gate freshness

gate:
	./scripts/check.sh

freshness:
	python3 scripts/check_freshness.py --max-age-days 8
