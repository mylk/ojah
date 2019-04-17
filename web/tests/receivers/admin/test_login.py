from django.http import HttpRequest
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
import mock
from web.receivers.admin import login


class LoginTestCase(TestCase):

    credentials = None
    logger = None
    request = None
    sender = None

    VALID_USERNAME = 'ojah'
    VALID_PASSWORD = 'ojah'

    def setUp(self):
        # retain the original imported packages
        login.logging_real = login.logging

        # mock method used by logging
        self.logger = mock.MagicMock()
        login.logging.getLogger = mock.MagicMock(return_value=self.logger)

        # mock the parameters to be passed to the receiver methods
        self.credentials = mock.MagicMock()
        self.request = HttpRequest()
        self.sender = mock.MagicMock()

    def tearDown(self):
        # revert the packages to the original imported
        login.logging = login.logging_real

    def admin_login_get(self):
        headers = {
            'user_agent': 'test-browser'
        }

        response = self.client.get(
            reverse('admin:login'),
            **headers
        )

        return response

    def admin_login_post(self, username, password):
        headers = {
            'user_agent': 'test-browser'
        }

        data = {
            'username': username,
            'password': password,
            'this_is_the_login_form': 1
        }

        response = self.client.post(
            reverse('admin:login'),
            data,
            **headers
        )

        return response

    def test_log_failed_login_logs_on_failed_login(self):
        # make a login post request with wrong password
        self.admin_login_post(self.VALID_USERNAME, 'foo')

        # the login failure was logged
        self.logger.warning.assert_called_once_with('Login failed from %s', '127.0.0.1')
        # no error was logged
        self.logger.error.assert_not_called()

    def test_log_failed_login_not_logs_on_sucessful_login(self):
        # make a login post request with correct password
        self.admin_login_post(self.VALID_USERNAME, self.VALID_PASSWORD)

        # no login failure was logged
        self.logger.warning.assert_not_called()
        # no error was logged
        self.logger.error.assert_not_called()

    def test_log_failed_login_not_logs_when_no_login(self):
        # make a login get request to retrieve the login page
        self.admin_login_get()

        # no login failure was logged
        self.logger.warning.assert_not_called()
        # no error was logged
        self.logger.error.assert_not_called()

    def test_log_failed_login_logs_remote_addr_when_x_forwarded_for_does_not_exist(self):
        # make the request contain only the REMOTE_ADDR value
        self.request.META['HTTP_X_FORWARDED_FOR'] = None
        self.request.META['REMOTE_ADDR'] = '192.168.1.1'

        # the method being tested
        login.log_failed_login(self.sender, self.credentials, self.request)

        # logged the failure with the REMOTE_ADDR value
        self.logger.warning.assert_called_once_with('Login failed from %s', '192.168.1.1')

    def test_log_failed_login_logs_x_forwarded_for_when_exists(self):
        # make the request contain both remote address values
        self.request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.2'
        self.request.META['REMOTE_ADDR'] = '192.168.1.1'

        # the method being tested
        login.log_failed_login(self.sender, self.credentials, self.request)

        # logged the failure with the HTTP_X_FORWARDED_FOR value
        self.logger.warning.assert_called_once_with('Login failed from %s', '192.168.1.2')

    def test_log_failed_login_handles_raised_exeption(self):
        # mock the request object
        self.request = mock.MagicMock()
        # force get() to raise an exception
        self.request.META.get = mock.MagicMock(side_effect=Exception('foo'))

        # the method being tested
        login.log_failed_login(self.sender, self.credentials, self.request)

        # no login failure was logged
        self.logger.warning.assert_not_called()
        # error was logged
        self.logger.error.assert_called_once_with('Could not log authentication failure.')
