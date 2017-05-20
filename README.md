Ojah!
=====

```Ojah!``` is a news aggregator that filters out the news to give you only those that are positive!

How it works
------------

A list of RSS feeds is provided to the application. The application crawls the feeds every now and then, stores the news
and then scores them by performing sentiment analysis on their title. Finally you have to subscribe to the RSS feed of
 ```Ojah!``` to get your positive news!


Technical information
---------------------

```Ojah!``` is written in python3 on top of the ```Django``` web framework. For sentiment analysis, the ```TextBlob```
module is being used.

The sentiment analysis module returns a value between ```-1``` and ```1``` where the first is a negative sentiment score
and the last one that of a positive sentiment. By default, news that are scored more than or equal to ```0.5``` are served by ```Ojah!```.

SQLite3 is used as the database of the project.

Use the application
-------------------

Currently, ```Ojah!``` is not served through the internet, but of course you can clone it and then use, distribute, or
hack it. To make it run on your computer:

- Download Django using your package manager
- Clone the application
- Install the dependencies of the project:

```
make deps
```

- Setup the database and the initial data:

```
make init
```

- Start the application:

```
./manage.py runserver
```

The application is now served by your localhost.

- Add the RSS feeds you want ```Ojah!``` to crawl using the administration panel at ```http://127.0.0.1:8000/admin```.
The default username is ```ojah``` and the password is ```ojah``` too.

- Trigger the crawling and scoring the news:

```
./manage.py crawl
```

- Point your favorite RSS reader at:

```
http://127.0.0.1:8000/rss
```