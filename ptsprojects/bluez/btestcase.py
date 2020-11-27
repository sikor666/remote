"""Test case that manages Maxwell IUT"""

from ptsprojects.testcase import TestCaseLT1, TestCaseLT2, TestFunc, TestFuncCleanUp

class BTestCase(TestCaseLT1):
    """A Bluez test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(BTestCase, self).__init__(*args, ptsproject_name="bluez", **kwargs)


class BTestCaseSlave(TestCaseLT2):
    """ BlueZ helper test case as a 2nd uint """

    def __init__(self, *args, **kwargs):
        """ Refer to TestCase.__init__ for parameters and their documentation"""

        super(BTestCaseSlave, self).__init__(*args, ptsproject_name="bluez", **kwargs)
