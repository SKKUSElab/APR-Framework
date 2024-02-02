import warnings
warnings.filterwarnings("ignore")

from .results import Results
from .testsuite import TestSuite
from .unittests import Running, Tracing, RunUnitTest

from ..utils import regularize, get_stmt_list
from ..transform import NodeParser

class Tester:
    def __init__(self, testcases:list, timeout:int=1):
        self.testsuite = TestSuite(testcases)
        self.timeout = timeout
    

    def split_test_hist(self, test_hist:dict) -> list:
        passed_tc_list = [tc_id for tc_id, result in test_hist.items() if result == 'Success']
        failed_tc_list = [tc_id for tc_id, result in test_hist.items() if result != 'Success']
        return passed_tc_list, failed_tc_list
    
    def is_all_fail(self, test_hist:dict) -> bool:
        return all(result != 'Success' for result in test_hist.values())
    
    def is_all_pass(self, test_hist:dict) -> bool:
        return all(result == 'Success' for result in test_hist.values())
    
    def get_tc_no_list(self) -> list:
        return self.testsuite.get_tc_no_list()
    
    def print_testcase(self, idx:int) -> str:
        return self.testsuite.print_testcase(idx)

    def __gen_test_code(self, code:str, input_tc:str, key_input:bool=False) -> str:
        try:
            test_input = input_tc
            if 'print(' not in input_tc:
                test_input = 'print(' + input_tc + ')'
            regularize(input_tc)
            regularize(test_input)
        except:
            key_input = True

        test_code = code.strip()
        if not key_input:
            if 'print(' not in input_tc:
                input_tc = 'print(' + input_tc + ')'
            test_code = code + '\n\n' + input_tc

        return regularize(test_code)
    
    
    def run(self, code:str, testcase:dict[str, str]={'input_tc':'', 'output_tc':''}, UnitTest=Running) -> tuple[str, str]:
        Results.init_global_vars()
        np = NodeParser()
        np.run(code)
        key_input = np.key_input
        Results.vari_names = np.var_name_list
        Results.timeout = self.timeout
        Results.input_tc = testcase['input_tc']
        Results.output_tc = testcase['output_tc']
        Results.test_code = self.__gen_test_code(code, testcase['input_tc'], key_input)
        rut = RunUnitTest()
        rut.run(UnitTest)

        # Exclude trace before testcase run
        loc = len(get_stmt_list(Results.test_code))
        try:
            start = Results.exec_traces.index(loc)
            del Results.exec_traces[:start+1]
        except: pass
        return Results.status, Results.output

    def validation(self, code:str) -> dict[int, str]:
        test_hist = {}

        code = regularize(code)
        for testcase in self.testsuite:
            self.run(code, testcase)
            testcase_no = testcase['testcase_no']
            test_hist[testcase_no] = Results.status
        
        return test_hist

    def trace(self, code:str) -> tuple[dict[int, str], dict[int, dict], dict[int, list]]:
        test_hist = {}
        vari_hist = {}
        trace_hist = {}

        code = regularize(code)
        for testcase in self.testsuite:
            self.run(code, testcase, Tracing)
            testcase_no = testcase['testcase_no']
            test_hist[testcase_no] = Results.status
            vari_hist[testcase_no] = Results.vari_traces
            trace_hist[testcase_no] = Results.exec_traces
        
        return test_hist, vari_hist, trace_hist