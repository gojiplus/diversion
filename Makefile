UV ?= uv
PYTHON_IMAGE ?= python:3.12-slim

.PHONY: sync lint test docs build test-wheel ci conformance ci-docker

sync:
	$(UV) sync --frozen --all-groups

lint:
	$(UV) run --frozen ruff check .
	$(UV) run --frozen ruff format --check .
	$(UV) run --frozen pyright
	$(UV)x --from pydoclint==0.9.1 pydoclint src/

test:
	$(UV) run --frozen pytest --cov --cov-report=term-missing

docs:
	$(UV) run --frozen --group docs sphinx-build -W -b html docs _site
	$(UV) run --frozen --group docs sphinx-build -W -b doctest docs _doctest

build:
	$(UV) build
	$(UV)x twine check dist/*

test-wheel: build
	@set -eu; \
	wheel_env=$$(mktemp -d); \
	trap 'rm -rf "$$wheel_env"' EXIT; \
	$(UV) venv "$$wheel_env/venv"; \
	$(UV) pip install --python "$$wheel_env/venv/bin/python" dist/*.whl --group test; \
	repo_dir="$(CURDIR)"; \
	cd "$$wheel_env"; \
	"$$wheel_env/venv/bin/python" -c 'import diversion; assert "/site-packages/" in diversion.__file__, diversion.__file__'; \
	"$$wheel_env/venv/bin/python" -m pytest --import-mode=append -c "$$repo_dir/pyproject.toml" "$$repo_dir/tests"

ci: sync lint test docs test-wheel

conformance:
	$(UV)x --from preen==0.6.2 preen check --strict --skip tests
	$(UV)x zizmor --min-severity high .github/workflows/

ci-docker:
	docker run --rm -v "$(CURDIR):/source:ro" -w /work $(PYTHON_IMAGE) sh -ec '\
		apt-get update -qq && apt-get install -y -qq --no-install-recommends git make libatomic1; \
		pip install --quiet uv; \
		tar -C /source --exclude=.git --exclude=.venv --exclude=.env \
			--exclude=dist --exclude=_site --exclude=_doctest --exclude=__pycache__ \
			--exclude=secrets.toml --exclude=".env.*" \
			-cf - . | tar -C /work -xf -; \
		make ci'
