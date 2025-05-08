.PHONY: all
all: lint

.PHONY: deps
deps: .deps-installed

.deps-installed: utils/install_dependencies.sh requirements.txt requirements-dev.txt
	utils/install_dependencies.sh
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
	tidy -config .htmltidy html/index.html
	npx prettier --check .
	ruff check .
	ruff format --diff .
	mypy --strict .

.PHONY: clean
clean:
	find . '(' -type f -name '*~' ')' -delete

.PHONY: deepclean
deepclean: clean
	rm -f .deps-installed
	rm -rf html/bootstrap-3.3.7-dist
	rm -rf html/jquery-3.2.1.min.js
	rm -rf html/jquery-ui-1.12.1
	rm -rf html/jquery-ui-themes-1.12.1
	rm -rf html/font-awesome-4.7.0
	rm -rf html/bootstrap.min.css
	rm -rf html/jquery.ui.touch-punch.min.js
