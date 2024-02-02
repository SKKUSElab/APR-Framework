import ast
from tqdm import tqdm
from ordered_set import OrderedSet
import numpy as np
import sqlite3
import time

from ..execution import Preprocess, FaultLocalization
from ..transform import VariableMap, SWTVariables, NodeMap, Fixer
from ..utils import regularize, Randoms, divide

table_dict = {'run_id':'INTEGER NOT NULL',
                  'generation':'INTEGER NOT NULL',
                  'p1_id':'TEXT',
                  'p1_code':'TEXT',
                  'p1_trace':'TEXT',
                  'p2_id':'TEXT',
                  'p2_code':'TEXT',
                  'p2_trace':'TEXT',
                  'varmap':'TEXT',
                  'testcase':'TEXT',
                  'suspicious':'TEXT',
                  'crossover':'TEXT',
                  'mutation':'TEXT',
                  'patch':'TEXT',
                  'fitness':'REAL',
                  'solution':'BLOB',
                  'time_sec':'REAL'}
foreign = 'FOREIGN KEY (run_id) REFERENCES run(id)'


class APR:
    def __init__(self, preproc:Preprocess, dbfile:str, table:str='log', foreign_id=None):
        self.foreign_id = foreign_id
        self.con = sqlite3.connect(dbfile)
        self.cur = self.con.cursor()
        self.__make_query(table)

        self.preproc = preproc
        self.tester = preproc.tester
        self.solutions = dict()
        self.max_dist = self.distance_from_max_points(-1, -1)

    def __make_query(self, table):
        self.cur.execute(f'SELECT COUNT(*) FROM sqlite_master WHERE name="{table}"')
        if self.cur.fetchone()[0] == 0:
            create_query = ", ".join([f'{key} {value}' for key, value in table_dict.items()])
            if foreign: create_query += f', {foreign}'
            self.cur.execute(f'CREATE TABLE {table} ({create_query});')
        insert_query = ", ".join([f':{key}' for key in table_dict.keys()])
        self.query = f'INSERT INTO {table} VALUES({insert_query});'
        self._query = {key:self.foreign_id if key == 'run_id' else None for key in table_dict.keys()}

    def __save_db(self):
        self.cur.execute(self.query, self._query)
        self._query = {key:self.foreign_id if key == 'run_id' else None for key in table_dict.keys()}
        self.con.commit()

    def population(self, pop_size:int, programs:dict) -> dict:
        # return {f'{file}_0':regularize(code) for file, code in programs.items()}
        file_list = list(programs.keys())
        sample_list = Randoms.sample(file_list, pop_size)
        return {f'{file}_0':regularize(programs[file]) for file in sample_list}
    
    def distance_from_max_points(self, x, y):
        return np.sqrt((1 - x)**2 + (1 - y)**2)
    
    def selection(self, p_id_1:str, populations:dict) -> str:
        p2 = None
        # Exclude p1 from population
        # Random Sampling population
        populations = {file:populations[file] 
                       for file in Randoms.sample(list(populations.keys()), len(populations)//2)
                       if file != p_id_1}
        
        # Tournament Selection
        max_score = 0
        for p_id_2 in populations.keys():
            score = self.fitness(p_id_1, p_id_2)
            if score > max_score:
                max_score = score
                p2 = p_id_2
            elif score == max_score:
                p2 = p_id_2 if p2 is None else Randoms.choice([p2, p_id_2])
        return p2
                        

    def modification(self, p_id_1:str, p_id_2:str) -> list:
        parent1, test_hist1, vari_hist1, trace_hist1 = self.preproc.run_data[p_id_1]
        parent2, test_hist2, vari_hist2, trace_hist2 = self.preproc.run_data[p_id_2]
        self._query['p1_code'] = parent1
        self._query['p2_code'] = parent2
        tree1 = ast.parse(parent1)
        tree2 = ast.parse(parent2)

        # Variable Variants
        tree2 = self.swt_variables(tree1, tree2, vari_hist1, vari_hist2)

        # Choice one random failed testcase for Exection Trace
        passed, failed = self.tester.split_test_hist(test_hist1)
        if failed: testcase = Randoms.choice(failed)
        ## Choice one random testcase if there is no failed testcase
        else: testcase = Randoms.choice(self.tester.get_tc_no_list())
        self._query['testcase'] = self.tester.print_testcase(testcase)
        
        ## Ordered Set Exection Traces
        traces1, traces2 = OrderedSet(trace_hist1[testcase]), OrderedSet(trace_hist2[testcase])
        self._query['p1_trace'] = str(list(traces1))
        self._query['p2_trace'] = str(list(traces2))

        # FaultLocalization
        fl = FaultLocalization()
        suspiciousness = fl.run_core(test_hist1, trace_hist1, formula='jaccard')
        suspicious = fl.get_fl_over_nscore(suspiciousness)
        self._query['suspicious'] = str(suspicious)
        traces1 = [lineno for lineno in traces1 if lineno in suspicious]

        # Crossover
        tree1 = self.crossover(tree1, traces1, tree2, traces2)

        # Mutation
        tree1 = self.mutation(tree1, traces1, tree2, traces2)
        
        child = ast.unparse(tree1)
        self._query['patch'] = child
        return regularize(child)
    
    def swt_variables(self, tree1, tree2, vari_hist1, vari_hist2):
        # Switch variables
        var_map = VariableMap(self.tester.get_tc_no_list()).run(tree1, vari_hist1, tree2, vari_hist2)
        self._query['varmap'] = str(var_map)
        tree2 = SWTVariables(var_map).visit(tree2)
        return tree2
    
    def crossover(self, tree1, traces1, tree2, traces2) -> ast:
        # Execution Trace Mapping
        node_map = NodeMap.crossover(tree1, traces1, tree2, traces2)
        self._query['crossover'] = str([(act,n1.lineno,n2.lineno) for n1, (act,n2) in node_map.items()])
        # Uniform Crossover
        tree1 = Fixer(node_map).visit(tree1)
        return tree1

    def mutation(self, tree1, traces1, tree2, traces2) -> ast:
        tree1 = ast.parse(ast.unparse(tree1))
        node_map = NodeMap.mutation(tree1, traces1, tree2, traces2)
        self._query['mutation'] = str([(act, n1.lineno, n2.lineno 
                        if n2 is not None else n1.lineno)
                        for n1, (act, n2) in node_map.items()])
        # Mutation
        tree1 = Fixer(node_map).visit(tree1)
        return tree1


    def fitness(self, p_id:str, c_id:str, child:str=None) -> float:
        # parent
        p_code, p_test_hist, p_vari_hist, p_trace_hist = self.preproc.run_data[p_id]
        
        # child
        if c_id not in self.preproc.run_data.keys():
            self.preproc.core_procs(c_id, child)
        c_code, c_test_hist, c_vari_hist, c_trace_hist = self.preproc.run_data[c_id]
        
        # Unit Test Score
        T = len(self.tester.testsuite)
        p_pass, p_fail = self.tester.split_test_hist(p_test_hist)
        c_pass, c_fail = self.tester.split_test_hist(c_test_hist)
        fp = set(p_fail) & set(c_pass)
        pp = set(p_pass) & set(c_pass)
        ff = set(p_fail) & set(c_fail)
        pf = set(p_pass) & set(c_fail)
        ut_score = (len(fp) + len(pp)*(T-1)/T + len(ff)*(1-T)/T - len(pf)) / T

        # Execution Trace Score
        et_score = 0
        for tc_no in self.tester.get_tc_no_list():
            p_traces = OrderedSet(p_trace_hist[tc_no])
            c_traces = OrderedSet(c_trace_hist[tc_no])
            
            trace_map = NodeMap.trace(p_code, p_traces, c_code, c_traces)
            lcs_trace = len(trace_map)
            max_trace = max(len(p_traces), len(c_traces))
            trace_sim = divide(lcs_trace, max_trace)

            if tc_no in fp:
                et_score += trace_sim
            elif tc_no in pp:
                et_score += trace_sim*(T-1)/T
            elif tc_no in ff:
                et_score += trace_sim*(1-T)/T
            else:
                et_score -= trace_sim
        et_score = divide(et_score, T)

        # Fitness Score
        score = self.max_dist - self.distance_from_max_points(ut_score, et_score)
        return score


    def run(self, programs:dict, pop_size:int=2, generations:int=50):
        populations = self.population(pop_size, programs)
        for generation in tqdm(range(1, generations+1), desc='Generation'):
            descendant = {}
            for p_id_1 in tqdm(populations.keys(), total=len(populations), desc='Popul', leave=False):
                start_time = time.process_time()

                self._query['generation'] = generation
                origin_p_id = p_id_1.rsplit("_", 1)[0]
                c_id = f'{origin_p_id}_{generation}'

                # Select mate parent
                p_id_2 = self.selection(p_id_1, populations)
                self._query['p1_id'] = p_id_1
                self._query['p2_id'] = p_id_2

                # Modification
                child = self.modification(p_id_1, p_id_2)

                # Calculate Fitness Score
                p_id = f'{p_id_1.rsplit("_", 1)[0]}_{generation-1}'
                p_score = self.fitness(p_id, p_id_1)
                c_score = self.fitness(p_id_1, c_id, child)
                self._query['fitness'] = c_score

                # Add solutions
                test_hist = self.preproc.run_data[c_id][1]
                if self.tester.is_all_pass(test_hist):
                    self.solutions.setdefault(origin_p_id, {})[generation] = child
                self._query['solution'] = self.tester.is_all_pass(test_hist)

                # Select next generation
                if p_score > c_score:
                    child = self.preproc.run_data[p_id][0]
                    self.preproc.core_procs(c_id, child)

                # Add descendant
                descendant[c_id] = child
                
                # Save DB
                self._query['time_sec'] = time.process_time() - start_time
                self.__save_db()

            # Initialize Population
            ## Delete data of previous generation
            for p_id in populations.keys():
                del self.preproc.run_data[p_id]
            self.preproc.trace_data = {k: 
                                       {i: j 
                                        for i, j in v.items() 
                                        if i not in populations.keys()} 
                                        for k, v in self.preproc.trace_data.items()}
            populations = descendant
        return self.solutions
    