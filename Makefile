lint: flake types test

flake:
	flake8 degreepath/ dp*.py

types:
	mypy --pretty degreepath/

test:
	pytest

watch:
	ptw

push: lint
	git push

validate:
	python3 dp-validate.py ../degreepath-areas/*/**.yaml --break

profile:
	echo 'use pyinstrument or py-spy'

