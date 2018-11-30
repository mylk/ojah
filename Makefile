deps_app:
	pip install -r requirements_app.txt

deps_worker_classify:
	pip install -r requirements_worker_classify.txt

deps_dev:
	pip install -r requirements_dev.txt

deps_corpora:
	python -m textblob.download_corpora

init:
	./manage.py makemigrations
	./manage.py migrate
	./manage.py loaddata initial_data
	./manage.py collectstatic --no-input

clean:
	find . -name *.pyc -delete
	find . -name __pycache__ -type d -delete

test: clean
	docker-compose run --rm app /bin/sh -c "./build/worker_classify/wait-for-rabbitmq.sh && ./manage.py test tests.rss.models"
	docker-compose run --rm app /bin/sh -c "./build/worker_classify/wait-for-rabbitmq.sh && ./manage.py test tests.rss.templatetags"
	docker-compose run --rm app /bin/sh -c "./build/worker_classify/wait-for-rabbitmq.sh && ./manage.py test tests.rss.views"
	docker-compose run --rm worker_classify /bin/sh -c "./build/worker_classify/wait-for-rabbitmq.sh && ./manage.py test tests.rss.management"
	docker-compose kill rabbitmq
