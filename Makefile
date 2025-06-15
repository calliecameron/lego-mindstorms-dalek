.PHONY: all
all: lint test

.PHONY: deps
deps: .deps-installed

.deps-installed: utils/install_dependencies.sh requirements.txt requirements-dev.txt package.json package-lock.json
	utils/install_dependencies.sh
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	npm install
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
	npx stylelint '**/*.css'
	npx eslint .
	npx prettier --check .
	ruff check .
	ruff format --diff .
	mypy --strict .

.PHONY: test
test: deps
	pytest --cov-report=term-missing --cov=dalek tests

.PHONY: clean
clean:
	find . '(' -type f -name '*~' ')' -delete

.PHONY: deepclean
deepclean: clean
	rm -f .deps-installed
	rm -rf node_modules
	rm -rf html/bootstrap-5.3.6-dist
	rm -rf html/jquery-3.7.1.min.js
	rm -rf html/jquery-ui-1.14.1
	rm -rf html/jquery-ui-themes-1.14.1
	rm -rf html/fontawesome-free-6.7.2-web
	rm -rf html/bootstrap.min.css
	rm -rf html/jquery.ui.touch-punch.js
