deps:
	pip install -r requirements.txt
	python -m textblob.download_corpora
	python -m nltk.downloader twitter_samples

deps_dev:
	pip install -r requirements_dev.txt

init:
	./manage.py makemigrations
	./manage.py migrate
	./manage.py loaddata initial_data
