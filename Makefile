.PHONY: all

all:
	python build_config.py
	docker run --interactive --rm quay.io/coreos/butane:release --pretty --strict < config.bu > config.ign
	python -m http.server 8000