import ast
from tqdm import tqdm

from .tester import Tester
from ..utils import regularize
from ..transform import NodeMap


class Preprocess:
    def __init__(self, tester:Tester):
        self.tester = tester

        self.run_data = {}
        self.trace_data = {}


    def get_run_data(self, code:str):
        code = regularize(code)
        test_hist, vari_hist, trace_hist = self.tester.trace(code)
        return code, test_hist, vari_hist, trace_hist
    
    def make_trace_data(self, p_id:str, code:str, test_hist:dict, trace_hist:dict):
        tree = ast.parse(code)
        line_node_map = NodeMap.get_line_node_map(tree)
        for testcase_no, result in test_hist.items():
            if result == 'Success':
                self.trace_data.setdefault(testcase_no, {})[p_id] = [
                    line_node_map[line] 
                    for line in trace_hist[testcase_no] 
                    if line in line_node_map.keys()]


    def core_procs(self, p_id:str, code:str):
        # Run Data
        code, test_hist, vari_hist, trace_hist = self.get_run_data(code)
        self.run_data[p_id] = code, test_hist, vari_hist, trace_hist

        # Trace Data
        self.make_trace_data(p_id, code, test_hist, trace_hist)

    def run(self, programs:dict):
        # Preprocessing Run Data
        for p_id, code in tqdm(programs.items(), total=len(programs), desc='Procs', leave=False):
            self.core_procs(f'{p_id}_0', code)

