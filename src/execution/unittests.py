import unittest
from io import StringIO
from unittest.mock import patch, mock_open
# from timeout_function_decorator import timeout
from timeout_decorator import timeout

from .results import Results
from .manager import Manager
from .tracer import Tracer

class TextTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super_class = super(TextTestResult, self)
        super_class.__init__(stream, descriptions, verbosity)
        self.status = 'Timed Out'
        self.output = Results.output_tc
    def addSuccess(self, test):
        super(TextTestResult, self).addSuccess(test)
        self.status = 'Success'
    def addError(self, test, err):
        super(TextTestResult, self).addError(test, err)
        self.status = 'Error'
        self.output = err[1].args[0]
    def addFailure(self, test, err):
        super(TextTestResult, self).addFailure(test, err)
        self.status = 'Failure'
        self.output = err[1].args[0]

class Running(unittest.TestCase):
    def setUp(self):
        self.input_data = StringIO(Results.input_tc)

    def assertEqual(self, actual, expected, msg=None):
        try:
            super().assertEqual(actual, expected, msg)
        except AssertionError as e:
            raise AssertionError(actual)

    @timeout(Results.timeout)
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    @Manager
    def test(self, mock_stdout, mock_stderr):
        with patch('sys.stdin', self.input_data):
            with patch('builtins.open', mock_open(read_data=Results.input_tc)):
                with patch('builtins.input', side_effect=self.input_data):
                    try: exec(Results.test_code)
                    except: pass
        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, Results.output_tc)


class Tracing(unittest.TestCase):
    def setUp(self):
        self.input_data = StringIO(Results.input_tc)

    def assertEqual(self, actual, expected, msg=None):
        try:
            super().assertEqual(actual, expected, msg)
        except AssertionError as e:
            raise AssertionError(actual)

    @timeout(Results.timeout)
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    @Manager
    def test(self, mock_stdout, mock_stderr):
        with patch('sys.stdin', self.input_data):
            with patch('builtins.open', mock_open(read_data=Results.input_tc)):
                with patch('builtins.input', side_effect=self.input_data):
                    try: Tracer().runctx(Results.test_code, globals())
                    except: pass
        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, Results.output_tc)


class RunUnitTest:
    def run(cls, UnitTest=Running):
        import sys

        backup_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            suite = unittest.TestLoader().loadTestsFromTestCase(UnitTest)
            runner = unittest.TextTestRunner(stream=StringIO())
            runner.resultclass = TextTestResult
            res = runner.run(suite)
            Results.status = res.status
            Results.output = res.output
        except Exception as e:
            Results.status = 'Error'
            Results.output = str(e)

        if sys.stdout != backup_stdout:
            sys.stdout.close()
            sys.stdout = backup_stdout