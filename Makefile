deps_app:
	pip install -r requirements_app.txt

deps_crawler:
	pip install -r requirements_crawler.txt

deps_dev:
	pip install -r requirements_dev.txt

deps_classifier:
	pip install -r requirements_classifier.txt

deps_corpora:
	python -m textblob.download_corpora lite
	python -c "import nltk; nltk.download('stopwords')"

makemigrations:
	docker-compose run --rm app /bin/sh -c "./manage.py makemigrations" ; \

init:
	./manage.py migrate
	./manage.py loaddata initial_data
	./manage.py collectstatic --no-input

analyze:
	docker-compose run --rm app /bin/sh -c "pylint --load-plugins=pylint_django --ignore=tests,migrations cli/ core/ web/" ; \
	docker-compose run --rm app /bin/sh -c "python -m pyt --adaptor Django ."
	docker-compose kill rabbitmq

clean:
	find . -name *.pyc -delete
	find . -name __pycache__ -type d -delete

test: clean
	docker-compose run --rm test
	docker-compose down
