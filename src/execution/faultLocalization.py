from .tester import Tester

class FaultLocalization:
    def __init__(self, success:str='Success'):
        self.__success = success

    def get_nth_fl(self, suspiciousness:dict, n:int=1):
        rankings = dict(sorted(suspiciousness.items(), key=lambda x:x[1], reverse=True))
        return list(rankings.keys())[n-1]
    
    def get_fl_over_nscore(self, suspiciousness:dict, n:int=0):
        fl_list = [lineno for lineno, score in suspiciousness.items() if score > n]
        return fl_list

    def trantula(self, test_hist:dict, trace_hist:dict) -> dict:
        total_pass = 0
        total_fail = 0
        pass_cnt_dict = {}
        fail_cnt_dict = {}
        lines = set()

        for testcase_no, status in test_hist.items():
            for lineno in set(trace_hist[testcase_no]):
                lines.add(lineno)
                if status != self.__success:
                    total_fail += 1
                    fail_cnt_dict.setdefault(lineno, 0)
                    fail_cnt_dict[lineno] += 1
                else:
                    total_pass += 1
                    pass_cnt_dict.setdefault(lineno, 0)
                    pass_cnt_dict[lineno] += 1
        
        suspiciousness = {}
        for lineno in lines:
            pass_cnt = pass_cnt_dict[lineno] if lineno in pass_cnt_dict.keys() else 0
            fail_cnt = fail_cnt_dict[lineno] if lineno in fail_cnt_dict.keys() else 0
            score = 0
            try: score = round((fail_cnt / total_fail) / ((fail_cnt / total_fail) + (pass_cnt / total_pass)), 1)
            except ZeroDivisionError:
                if fail_cnt > 0 and pass_cnt == 0:
                    score = 1
            suspiciousness[lineno] = score
        
        return suspiciousness
    
    def jaccard(self, test_hist:dict, trace_hist:dict) -> dict:
        total_fail = 0
        exec_cnt_dict = {}
        fail_cnt_dict = {}
        lines = set()

        for testcase_no, status in test_hist.items():
            if status != self.__success:
                total_fail += 1
            for lineno in set(trace_hist[testcase_no]):
                lines.add(lineno)
                exec_cnt_dict.setdefault(lineno, 0)
                exec_cnt_dict[lineno] += 1
                if status != self.__success:
                    fail_cnt_dict.setdefault(lineno, 0)
                    fail_cnt_dict[lineno] += 1
        
        suspiciousness = {}
        for lineno in lines:
            exec_cnt = exec_cnt_dict[lineno] if lineno in exec_cnt_dict.keys() else 0
            fail_cnt = fail_cnt_dict[lineno] if lineno in fail_cnt_dict.keys() else 0
            score = 0
            try: score = round((fail_cnt / (exec_cnt + (total_fail - fail_cnt))), 1)
            except ZeroDivisionError:
                if fail_cnt > 0 and exec_cnt == 0:
                    score = 1
            suspiciousness[lineno] = score
        
        return suspiciousness
    
    def run_core(self, test_hist:dict, trace_hist:dict, formula:str="jaccard") -> dict:
        if formula == "trantula":
            suspiciousness = self.trantula(test_hist, trace_hist)
        elif formula == "jaccard":
            suspiciousness = self.jaccard(test_hist, trace_hist)
        return suspiciousness
    
    def run(self, code:str, tester:Tester, formula:str="jaccard") -> dict:
        test_hist, _, trace_hist = tester.trace(code)
        suspiciousness = self.run_core(test_hist, trace_hist, formula)
        return suspiciousness