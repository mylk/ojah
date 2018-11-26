deps_app:
	pip install -r requirements_app.txt

deps_worker_classify:
	pip install -r requirements_worker_classify.txt
	python -m textblob.download_corpora

deps_dev:
	pip install -r requirements_dev.txt

init:
	./manage.py makemigrations
	./manage.py migrate
	./manage.py loaddata initial_data
	./manage.py collectstatic --no-input

clean:
	find . -name *.pyc -delete
	find . -name __pycache__ -type d -delete

test: clean
	docker-compose run --rm app ./manage.py test
