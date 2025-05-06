.PHONY: all
all: clean

.PHONY: clean
clean:
	find . '(' -type f -name '*~' ')' -delete
