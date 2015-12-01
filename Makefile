test:
	@cd tests; PYTHONPATH=.. nosetests

release:
	python setup.py sdist bdist_wheel upload
