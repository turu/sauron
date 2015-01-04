run:
	twistd -n sauron

cov:
	coverage run --branch --source sauron  `which trial` tests
	coverage report
	coverage html

.PHONY: run cov