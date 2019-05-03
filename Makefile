# convenience makefile

.DEFAULT_GOAL := .installed

.PHONY: deploy
deploy:
	@pipenv run python -m silver_spork.main deploy

.PHONY: destroy
destroy:
	@pipenv run python -m silver_spork.main destroy

.PHONY: help
help:
	@echo "Usage: make [target]\n"
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'

install:
	@rm -f .installed  # force re-install
	@make .installed

.installed: Pipfile Pipfile.lock
	@echo "Pipfile(.lock) is newer than .installed, (re)installing"
	@pipenv install --python `which python3.7` --dev
	@echo "This file is used by 'make' for keeping track of last install time. If Pipfile or Pipfile.lock are newer then this file (.installed) then all 'make *' commands that depend on '.installed' know they need to run pipenv install first." > .installed


.PHONY: clean
clean:
	@pipenv --rm

.PHONY: sort
sort:
	@git ls-files '*.py' | xargs pipenv run isort -rc -fas -sl

