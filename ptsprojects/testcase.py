"""PTS test case python implementation"""

import shlex
import os
import subprocess
import re
import sys
import time
import logging
from threading import Thread
import Queue
import datetime
import errno
import ptstypes

log = logging.debug


class MmiParser(object):
    """"Interface to parsing arguments from description of MMI

    It is assumed that all arguments in description are enclosed in single
    quotes.

    """

    min_arg = 1
    # hopefully this is the max number of arguments in MMI description
    max_arg = 10

    arg_name_prefix = "arg_"
    arg_value_prefix = "MMI_arg_value_"

    def __init__(self):
        """Constructor of the parser"""

        # pattern used to search for args in MMI description
        self.pattern = re.compile(r"(?:'|=\s+)([0-9-xA-Fa-f]+)")

        # list of the parsed argument values from MMI description
        self.args = []

        # create attributes to reference the args
        for i in range(self.min_arg, self.max_arg):
            index = str(i)
            mmi_arg_name = self.arg_name_prefix + index
            mmi_arg_value = self.arg_value_prefix + index
            setattr(self, mmi_arg_name, mmi_arg_value)

    def parse_description(self, description):
        """Parse PTS MMI description text for argument values.

        It is necessary to do it for now, but in future PTS will provide API to
        get the values

        An example of MMI that requires parsing is listed below. For that MMI
        00D3 should be converted to hexadecimal 0xD3 and size to int 45

        project_name: GATT
        wid: 69
        test_case_name: TC_GAC_CL_BV_01_C

        Please send prepare write request with handle = '00D3'O and size = '45'
        to the PTS.

        Description: Verify that the Implementation Under Test (IUT) can send
        data according to negotiate MTU size."

        """
        log("%s %r", self.parse_description.__name__, description)

        self.args = self.pattern.findall(description)

        log("Parse result: %r", self.args)

    def reset(self):
        """Resets the args

        To be used when parsed values are not needed anymore

        """
        self.args = []

    def process_args(self, args):
        """Replaces the MMI keywords arguments (e.g. MMI.arg_1) with the
        respective argument values from MMI description

        """
        log("%s: %s", self.process_args.__name__, args)
        log("MMI.args now %r", self.args)

        args_list = list(args)

        for arg_index, arg in enumerate(args):
            if not isinstance(arg, basestring):  # omit not strings
                continue

            if arg.startswith(MMI.arg_value_prefix):
                mmi_index = int(arg[arg.rfind("_") + 1:])

                args_list[arg_index] = self.args[mmi_index - 1]

        out_args = tuple(args_list)
        log("returning %r", out_args)
        return out_args


MMI = MmiParser()


class AbstractMethodException(Exception):
    """Exception raised if an abstract method is called."""
    pass


class PTSCallback(object):
    """Base class for PTS callback implementors"""

    def __init__(self):
        pass

    def log(self, log_type, logtype_string, log_time, log_message):
        """Implements:

        interface IPTSControlClientLogger : IUnknown {
            HRESULT _stdcall Log(
                            [in] _PTS_LOGTYPE logType,
                            [in] LPWSTR szLogType,
                            [in] LPWSTR szTime,
                            [in] LPWSTR pszMessage);
        };
        """
        raise AbstractMethodException()


class TestCase(PTSCallback):
    """A PTS test case"""

    def copy(self):
        """Copy constructor"""
        return TestCase(self.project_name, self.name, self.ptsproject_name,
                        self.log_filename, self.log_dir)

    def __init__(self, project_name, test_case_name,
                 ptsproject_name=None, log_filename=None, log_dir=None):
        """TestCase constructor"""

        self.project_name = project_name
        self.name = test_case_name
        # a.k.a. final verdict
        self.status = "init"
        self.state = None

        self.thread_exception = Queue.Queue()
        self.ptsproject_name = ptsproject_name
        self.log_filename = log_filename
        self.log_dir = log_dir

    def reset(self):
        self.status = "init"
        self.state = None

    def __str__(self):
        """Returns string representation"""
        return "%s %s" % (self.project_name, self.name)

    def initialize_logging(self, session_logging_dir):
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        normalized_name = self.name.replace('/', '_')
        timestamp_name = "%s_%s" % (normalized_name, now)
        test_log_dir = os.path.join(session_logging_dir, timestamp_name)
        try:
            os.makedirs(test_log_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        log("Created logs directory %r", test_log_dir)

        self.log_dir = test_log_dir
        self.log_filename = os.path.join(test_log_dir, timestamp_name + ".log")

    def log(self, log_type, logtype_string, log_time, log_message):
        """Overrides PTSCallback method. Handles
        PTSControl.IPTSControlClientLogger.Log"""

        new_status = None

        # mark test case as started
        if log_type == ptstypes.PTS_LOGTYPE_START_TEST:
            new_status = "Started"

        # mark the final verdict of the test case
        # check for "final verdict" to avoid "Encrypted Verdict"
        # it could be 'Final verdict' or 'Final Verdict'
        elif log_type == ptstypes.PTS_LOGTYPE_FINAL_VERDICT and \
                logtype_string.lower() == "final verdict":

            if "PASS" in log_message:
                new_status = "PASS"
            elif "INCONC" in log_message:
                new_status = "INCONC"
            elif "FAIL" in log_message:
                new_status = "FAIL"
            else:
                new_status = "UNKNOWN VERDICT: %s" % log_message.strip()

        if new_status:
            self.status = new_status
            log("New status %s - %s", str(self), new_status)


class TestCaseLT1(TestCase):
    def copy(self):
        """Copy constructor"""

        test_case = super(TestCaseLT1, self).copy()
        test_case.name_lt2 = self.name_lt2

        return test_case

    def __init__(self, *args, **kwargs):
        name_lt2 = kwargs.pop('lt2', None)
        super(TestCaseLT1, self).__init__(*args, **kwargs)
        self.name_lt2 = name_lt2


class TestCaseLT2(TestCase):
    pass
