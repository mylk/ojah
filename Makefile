deps_app:
	pip install -r requirements_app.txt

deps_crawler:
	pip install -r requirements_crawler.txt

deps_dev:
	pip install -r requirements_dev.txt

deps_worker_classify:
	pip install -r requirements_worker_classify.txt

deps_corpora:
	python -m textblob.download_corpora lite
	python -c "import nltk; nltk.download('stopwords')"

init:
	./manage.py migrate
	./manage.py loaddata initial_data
	./manage.py collectstatic --no-input

analyze:
	docker-compose run --rm app /bin/sh -c "pylint --load-plugins=pylint_django --ignore=tests,migrations core/ management/ rss/" ; \
	docker-compose run --rm app /bin/sh -c "python -m pyt --adaptor Django ."
	docker-compose kill rabbitmq

clean:
	find . -name *.pyc -delete
	find . -name __pycache__ -type d -delete

test: clean
	docker-compose run --rm test
