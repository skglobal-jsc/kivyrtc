#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from kivyrtc.app import KivyRTCApp


class TestKivyRTCApp(unittest.TestCase):
    """TestCase for KivyRTCApp.
    """
    def setUp(self):
        self.app = KivyRTCApp()

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
