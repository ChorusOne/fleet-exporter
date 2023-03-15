.PHONY: srccheck

srccheck: mypy black pylint

mypy:
	mypy --strict fleet-exporter.py

black:
	black --check fleet-exporter.py

pylint:
	pylint --disable=C0103,W1203 fleet-exporter.py
