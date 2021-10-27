"""
https://github.com/kevin1024/vcrpy
mixin example:
https://github.com/agriffis/vcrpy-unittest/

USAGE:
from utils.vcr import VCRMixin
super().setUp()
"""

import os
import inspect

import vcr

from django.conf import settings



class VCRMixin(object):
    """A mixin for TestCase that provides VCR integration.

    DOCS: https://vcrpy.readthedocs.io/en/latest/usage.html#record-modes
    """

    def setUp(self):
        super(VCRMixin, self).setUp()

        if not settings.TESTS_VCR_FOR_REQUESTS_ENABLED:
            return

        my_vcr = vcr.VCR(
            cassette_library_dir=os.path.join(settings.PROJECT_DIR, 'cassettes'),
            record_mode='once',  # show errors if new requests in test
        )
        # print(self._get_cassette_name())
        cm = my_vcr.use_cassette(self._get_cassette_name())
        self.cassette = cm.__enter__()
        self.addCleanup(cm.__exit__, None, None, None)

    def _get_cassette_name(self):
        return "%s.%s.%s.yaml" % (
            self.__module__,
            self.__class__.__name__,
            self._testMethodName
        )

    def _get_cassette_library_dir(self):
        """
        to have 'cassettes/' directory in each app
        """
        testdir = os.path.dirname(inspect.getfile(self.__class__))
        return os.path.join(testdir, 'cassettes')

