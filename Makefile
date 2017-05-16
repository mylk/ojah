deps:
	sudo pip install -r requirements

deps-dev:
	sudo pip install -r requirements_dev

init:
	./manage.py makemigrations
	./manage.py migrate
