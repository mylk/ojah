# Ojah!

`Ojah!` is a news aggregator that filters out the news to give you only those that are positive!

## How it works

A list of RSS feeds is provided to the application. The application crawls the feeds every now and then, stores the news
and then scores them by performing sentiment analysis on their title. Finally, you have to visit the web page of `Ojah!`
or subscribe to the RSS feed to get your positive news!


## Technical information

`Ojah!` is written in python3 on top of the `Django` web framework. For sentiment analysis, the `TextBlob`
module is being used.

### The components

Currently the components are three:

- web app
- crawler
- classifier

Each one is placed on a separate Docker container, in case more than one instance is required for any of them.

### Sentiment analysis

The sentiment analysis classifier currently returns either the `neg` or the `pos` value for negative or positive
result respectively. News that are scored with `pos` are served by `Ojah!`.

### Used classifier

Unfortunatelly, the default classifier which I initially used, was not that accurate. I ran a comparison for a short
period of time to find the most accurate between:

- TextBlob "default" sentiment polarity classifier
- TextBlob "NaiveBayesClassifier" classifier
- vaderSentiment "SentimentIntensityAnalyzer" classifier

The most accurate was "NaiveBayesClassifier" which I finally kept.

### Corpora

I initially used the Twitter corpora provided by the `nltk` module. Then I used only the corpora produced
by `Ojah!` to improve the accuracy of the classification.

Custom corpora can be added using the administration dashboard of `Ojah!` where we can change the classification
of a news item and use it as a corpus, in order to make `Ojah!` learn from its mistakes.

### Used database

Previously an embedded database was used (SQLite3), but for the case of the need to scale any of the components
(app, crawler, classifier), a migration to MySQL was performed.

## Use the application

Of course you can clone it and then use, distribute, or hack it.

You can either run it in your host or use Docker to run it in containers (the Docker container recipes are included).
In any case, you firstly have to clone this repository.

### Host installation

So, you are a traditional type of guy. For this installation you should:

- Install the dependencies of the project:

```
make deps_app
make deps_corpora
make deps_crawler
make deps_worker_classify
```

- Setup the database, the initial data and static files:

```
make init
```

- Start the application:

```
./manage.py runserver
```

- Trigger the crawling of the news items:

```
./manage.py crawl
```

- Trigger the classification of the news items:

```
./manage.py classify
```

### Run in containers

So you love containers like me. Things are really simple here, you can have everything being ran
with a couple of commands:

- Build the images (will take a few minutes for the first build):

```
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
```

- Start the containers:

```
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Last but not least

Irrelevant to the environment you run the application (your host or containers) the application can
be visited at `http://127.0.0.1:8000`.

- Add the RSS feeds you want `Ojah!` to crawl using the administration dashboard at `http://127.0.0.1:8000/admin`.
The default username is `ojah` and the password is `ojah`` too.

- Point your favorite RSS reader at:

```
http://127.0.0.1:8000/rss
```

- There is also a web interface (clone of [Hacker news](https://news.ycombinator.com/)) to see the news from your web browser:

```
http://127.0.0.1:8000/web
```

The administration dashboard has a few more cool things, like statistics and a simple graph for classification accuracy.

## Hack it!

If you are hacking using the host environment (instead of containers), you will need to install the development
environment dependencies too:

```
make deps_dev
```

In case you are hacking using the containers, replace "docker-compose.prod.yml" with "docker-compose.dev.yml"
in the above commands to include debugging, testing and linting tools.

Also, irrelevant to the environment you run the application (your host or containers), you can run the tests by running:


```
make test
```

This will run the tests in a separate "test" container.


You can also run a linting process:

```
make analyze
```
