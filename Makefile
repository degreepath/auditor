all: lint

lint: flake mypy test
check: lint

flake:
	flake8 --show-source --statistics degreepath/ *.py

mypy:
	mypy --pretty degreepath/ *.py

test:
	pytest tests/ degreepath/

watch:
	ptw

push: lint
	git push

validate:
	python3 dp-validate.py ../degreepath-areas/*/**.yaml --break

profile:
	echo 'use pyinstrument or py-spy'

nuitka:
	python3 -m nuitka --standalone --follow-imports --plugin-enable=pylint-warnings --python-flag=no_site --warn-unusual-code --warn-implicit-exceptions dp.py
