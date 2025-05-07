.PHONY: all
all: lint

.PHONY: deps
deps: .deps-installed

.deps-installed: requirements.txt requirements-dev.txt
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	touch .deps-installed

requirements.txt: requirements.in pyproject.toml
	pip-compile -q

requirements-dev.txt: requirements-dev.in pyproject.toml
	pip-compile -q requirements-dev.in

.PHONY: lint
lint: deps
	utils/find_shell_files.sh | xargs -d '\n' shellcheck
	utils/find_shell_files.sh | xargs -d '\n' shfmt -l -d -i 4
	ruff check .
	ruff format --diff .
	mypy --strict .

.PHONY: clean
clean:
	find . '(' -type f -name '*~' ')' -delete
