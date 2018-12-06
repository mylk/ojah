from django.test import TestCase
import mock
from rss.management.commands import classify


class CommandTestCase(TestCase):

    command = None

    def setUp(self):
        self.command = classify.Command()

    def test_handle_fails_when_classifier_training_fails(self):
        pass

    def test_handle_starts_training_the_classifier_and_starts_threads(self):
        pass

    def test_classify_consumer_handles_exception_when_starting_consuming_the_queue(self):
        pass

    def test_classify_consumer_consumes_the_classify_queue_with_the_classify_callback(self):
        pass

    def test_train_consumer_handles_exception_when_starting_consuming_the_queue(self):
        pass

    def test_train_consumer_consumes_the_train_queue_with_the_train_callback(self):
        pass

    def test_get_consumer_handles_exception_when_connecting_to_broker(self):
        pass

    def test_get_consumer_returns_channel_to_consume_the_classify_queue(self):
        pass

    def test_get_consumer_returns_channel_to_consume_the_train_queue(self):
        pass

    def test_get_classifier_prepares_shuffled_corpora_and_returns_naive_bayes_classifier(self):
        pass

    def test_classify_callback_waits_for_classifier_when_no_trained_classifier_exists(self):
        pass

    def test_classify_callback_handles_exceptions_when_classifing(self):
        pass

    def test_classify_callback_classifies_negative_queue_item_and_saves_on_database(self):
        pass

    def test_classify_callback_classifies_positive_queue_item_and_saves_on_database(self):
        pass

    def test_classify_callback_auto_publishes_news_item_when_auto_publish_is_enabled(self):
        pass

    def test_train_callback_purges_queue_and_trains_classifier(self):
        pass
