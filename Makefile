all: lint

lint: flake mypy test
check: lint

flake:
	flake8 --show-source --statistics dp/

mypy:
	mypy --pretty --show-error-codes dp/

test:
	pytest tests/ dp/

watch:
	ptw

push: lint
	git push

validate:
	python3 -m dp.bin.validate ../degreepath-areas/*/**.yaml --break

profile:
	echo 'use pyinstrument'
	echo 'or use py-spy'

nuitka:
	python3 -m nuitka --standalone --follow-imports --plugin-enable=pylint-warnings --python-flag=no_site --warn-unusual-code --warn-implicit-exceptions dp/__main__.py
