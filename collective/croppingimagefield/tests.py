import unittest
import os

from Globals import InitializeClass, package_home

from zope.testing import doctestunit
from zope.component import testing
from Testing import ZopeTestCase as ztc

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
ptc.setupPloneSite()

import collective.croppingimagefield

class TestCase(ptc.PloneTestCase):
    def afterSetUp(self):
        PACKAGE_HOME = package_home(globals())
        imgpath = os.path.join(PACKAGE_HOME, 'test.gif')
        self._image = open(imgpath).read()

def test_suite():
    return unittest.TestSuite([
        ztc.FunctionalDocFileSuite(
            'README.txt', package='collective.croppingimagefield',
            test_class=TestCase),
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
