"""Test the __init__.py module"""

import unittest
from hamcrest import assert_that, contains_string

from .. import __version__


class TestInit(unittest.TestCase):
    """Tests for the __init__.py module"""

    def test_version(self):
        """Version has a . in it"""
        assert_that(__version__, contains_string("."))
