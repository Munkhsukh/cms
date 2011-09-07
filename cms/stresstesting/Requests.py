#!/usr/bin/python
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2010-2011 Giovanni Mascellani <mascellani@poisson.phc.unipi.it>
# Copyright © 2010-2011 Stefano Maggiolo <s.maggiolo@gmail.com>
# Copyright © 2010-2011 Matteo Boscariol <boscarim@hotmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time
import re
import urllib

class TestRequest:
    """Docstring TODO.

    """

    OUTCOME_SUCCESS   = 'success'
    OUTCOME_FAILURE   = 'failure'
    OUTCOME_UNDECIDED = 'undecided'
    OUTCOME_ERROR     = 'error'

    def __init__(self, browser, base_url=None):
        if base_url is None:
            base_url = 'http://localhost:8888/'
        self.browser = browser
        self.base_url = base_url
        self.outcome = None

        self.start_time = None
        self.stop_time = None

    def execute(self):

        # Execute the test
        description = self.describe()
        try:
            self.start_time = time.time()
            self.do_request()
            self.stop_time = time.time()
            success = self.test_success()

        # Catch possible exceptions
        except Exception as exc:
            if self.stop_time is None:
                self.stop_time = time.time()
            print >> sys.stderr, "Request '%s' terminated " \
                "with an exception: %s" % (description, repr(exc))
            self.outcome = TestRequest.OUTCOME_ERROR

        # If no exceptions were casted, decode the test evaluation
        else:

            # Could not decide on the evaluation
            if success is None:
                print >> sys.stderr, "Could not determine " \
                    "status for request '%s'" % (description)
                self.outcome = TestRequest.OUTCOME_UNDECIDED

            # Success
            elif success:
                print >> sys.stderr, "Request '%s' successfully " \
                    "completed" % (description)
                self.outcome = TestRequest.OUTCOME_SUCCESS

            # Failure
            elif not success:
                print >> sys.stderr, "Request '%s' failed" % (description)
                self.outcome = TestRequest.OUTCOME_FAILURE

    def describe(self):
        raise NotImplementedError("Please subclass this class "
                                  "and actually implement some request")

    def do_request(self):
        raise NotImplementedError("Please subclass this class "
                                  "and actually implement some request")

    def test_success(self):
        raise NotImplementedError("Please subclass this class "
                                  "and actually implement some request")

    def store_to_file(self, fd):
        raise NotImplementedError("Please subclass this class "
                                  "and actually implement some request")


class GenericRequest(TestRequest):
    """Docstring TODO.

    """
    MINIMUM_LENGTH = 100

    def __init__(self, browser, base_url=None):
        TestRequest.__init__(self, browser, base_url)
        self.url = None
        self.data = None

    def do_request(self):
        if self.data is None:
            self.response = self.browser.open(self.url)
        else:
            self.response = self.browser.open(self.url,
                                              urllib.urlencode(self.data))
        self.res_data = self.response.read()

    def test_success(self):
        #if self.response.getcode() != 200:
        #    return False
        if len(self.res_data) < GenericRequest.MINIMUM_LENGTH:
            return False
        return True

    def store_to_file(self, fd):
        print >> fd, "Test type: %s" % (self.__class__.__name__)
        print >> fd, "Execution start time: %f" % (self.start_time)
        print >> fd, "Execution stop time: %f" % (self.stop_time)
        print >> fd, "Duration: %f seconds" % (self.stop_time - self.start_time)
        print >> fd, "Outcome: %s" % (self.outcome)
        fd.write(self.specific_info())
        print >> fd
        fd.write(self.res_data)

    def specific_info(self):
        return ''


class HomepageRequest(GenericRequest):
    """Load the main page of CWS.

    """
    def __init__(self, http_helper, username, loggedin, base_url=None):
        GenericRequest.__init__(self, http_helper, base_url)
        self.url = self.base_url
        self.username = username
        self.loggedin = loggedin

    def describe(self):
        return "check the main page"

    def test_success(self):
        if not GenericRequest.test_success(self):
            return False
        username_re = re.compile(self.username)
        if self.loggedin:
            if username_re.search(self.res_data) is None:
                return False
        else:
            if username_re.search(self.res_data) is not None:
                return False
        return True


class LoginRequest(GenericRequest):
    """Try to login to CWS with given credentials.

    """
    def __init__(self, http_helper, username, password, base_url=None):
        TestRequest.__init__(self, http_helper, base_url)
        self.username = username
        self.password = password
        self.url = self.base_url + 'login'
        self.data = {'username': self.username,
                     'password': self.password,
                     'next': '/'}

    def describe(self):
        return "try to login"

    def test_success(self):
        if not GenericRequest.test_success(self):
            return False
        fail_re = re.compile('Failed to log in.')
        if fail_re.search(self.res_data) is not None:
            return False
        username_re = re.compile(self.username)
        if username_re.search(self.res_data) is None:
            return False
        return True

    def specific_info(self):
        return 'Username: %s\nPassword: %s\n' % (self.username, self.password)
