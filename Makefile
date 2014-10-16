tests: test

test:
	sh mk_test_files.sh
	python -m unittest discover -v tests
