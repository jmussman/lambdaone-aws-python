# test_hello_world.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

from unittest import TestCase

from lambdaone import hello_world

class TestHelloWorld(TestCase):

    def test_hello_world(self):

        result = hello_world.hello()

        self.assertIn('Hello, World!', result)