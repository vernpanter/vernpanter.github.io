# GitHub Pages is on Ruby 3.3, which Homebrew does not put on PATH. Exporting
# PATH is not enough, the make on MacOS ignores it when it looks up a command.
BREW_RUBY := $(shell command -v brew >/dev/null 2>&1 && brew --prefix ruby@3.3 2>/dev/null)
ifneq ($(wildcard $(BREW_RUBY)/bin/ruby),)
RUBY_ENV := env PATH="$(BREW_RUBY)/bin:$$PATH"
endif
PORT ?= $(or $(WORKFLOW_PORT_BASE),40100)

.PHONY: setup check test types images build serve clean

setup:
	$(RUBY_ENV) bundle install
	uv sync
	git config core.hooksPath .githooks

# Everything CI and the hooks run
check: types
	uv run actionlint
	uv run python scripts/check_site.py
	$(RUBY_ENV) uv run python -m unittest discover -s tests
	$(MAKE) build
	uv run python scripts/check_site.py --built _site

types:
	uv run pyright

test:
	uv run python -m unittest discover -s tests -p 'test_scripts.py'

images:
	uv run python scripts/prepare_images.py

# The uploads are left out of the published site, only the copies go up
build: images
	$(RUBY_ENV) bundle exec jekyll build --strict_front_matter
	rm -rf _site/art

serve: images
	$(RUBY_ENV) bundle exec jekyll serve --port $(PORT)

clean:
	rm -rf _site derived _data/images.json .jekyll-cache
