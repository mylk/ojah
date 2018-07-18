deps:
	pip install -r requirements.txt

deps_dev:
	pip install -r requirements_dev.txt

init:
	./manage.py makemigrations
	./manage.py migrate
	./manage.py loaddata initial_data