.PHONY: all
all: lint

.PHONY: lint
lint:
	utils/find_shell_files.sh | xargs -d '\n' shellcheck
	utils/find_shell_files.sh | xargs -d '\n' shfmt -l -d -i 4

.PHONY: clean
clean:
	find . '(' -type f -name '*~' ')' -delete
