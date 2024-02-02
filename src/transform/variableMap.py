import pylcs
import ast
from ordered_set import OrderedSet

from .nodeParser import NodeParser

from ..utils import Randoms


class VariableMap:
    def __init__(self, tc_id_list:list=[]):
        self.var_map = {}
        self.tc_id_list = tc_id_list
        self.non_used_a_var_list = []


    def __init_non_used_var(self):
        self.non_used_a_var_list = [a_var for a_var in self.a_var_name_list if a_var not in self.var_map.values()]


    def dea_var_map(self):
        # Map variables based on dynamic equivalence analysis
        a_var_set = OrderedSet()
        for tc_id in self.tc_id_list:
            for var in self.a_var_hist[tc_id].keys():
                a_var_set.add(var)
        b_var_set = OrderedSet()
        for tc_id in self.tc_id_list:
            for var in self.b_var_hist[tc_id].keys():
                b_var_set.add(var)
        for b_var in b_var_set:
            for a_var in a_var_set:
                is_matched = True
                for tc_id in self.tc_id_list:
                    b_in = b_var in self.b_var_hist[tc_id].keys()
                    a_in = a_var in self.a_var_hist[tc_id].keys()
                    if not b_in and not a_in:
                        continue
                    elif b_in and not a_in:
                        is_matched = False
                        break
                    elif not b_in and a_in:
                        is_matched = False
                        break
                    else:
                        b_var_values = self.b_var_hist[tc_id][b_var]
                        a_var_values = self.a_var_hist[tc_id][a_var]
                        if not self.__is_hist_equal(b_var_values, a_var_values):
                            is_matched = False
                            break
                if is_matched:
                    if b_var not in self.var_map.keys():
                        self.var_map[b_var] = a_var
        return self.var_map
    
    def __is_hist_equal(self, hist_a, hist_b):
        if len(hist_a) != len(hist_b):
            return False
        for i in range(len(hist_a)):
            if not self.__is_equal(hist_a[i], hist_b[i]):
                return False
        return True

    def __is_equal(self, object_a, object_b):
        if str(type(object_a)) == str(type(object_b)):
            if object_a == object_b:
                return True
            else:
                return False
        else:
            close_type_list = ["<class 'list'>", "<class 'tuple'>"]
            if str(type(object_a)) in close_type_list and \
                    str(type(object_b)) in close_type_list:
                if list(object_a) == list(object_b):
                    return True
                else:
                    return False
            else:
                return False
            

    def lcs_var_map(self) -> dict:
        # Map variables based on longest common subsequence
        self.__init_non_used_var()
        for b_var in self.b_var_name_list:
            if b_var not in self.var_map.keys() and self.non_used_a_var_list:
                cand_var = {}
                for a_var in self.non_used_a_var_list:
                    lcs = pylcs.lcs_sequence_length(a_var, b_var)
                    cand_var.setdefault(lcs, []).append(a_var)
                if not cand_var: continue
                max_lcs = max(list(cand_var.keys()))
                a_var = Randoms.choice(cand_var[max_lcs])
                self.var_map[b_var] = a_var
                self.non_used_a_var_list.remove(a_var)
        return self.var_map
    

    def type_var_map(self):
        # Map variables with same type
        self.__init_non_used_var()

        a_var_type_dict = self.get_var_type_dict(self.a_var_hist)
        b_var_type_dict = self.get_var_type_dict(self.b_var_hist)

        for b_var, b_type in b_var_type_dict.items():
            if b_var not in self.var_map.keys() and self.non_used_a_var_list:
                cand_var_list = [a_var 
                                 for a_var in self.non_used_a_var_list 
                                 if a_var in a_var_type_dict.keys() \
                                    and a_var_type_dict[a_var] == b_type]
                if not cand_var_list: continue
                a_var = Randoms.choice(cand_var_list)
                self.var_map[b_var] = a_var
                self.non_used_a_var_list.remove(a_var)
        return self.var_map
    
    def get_var_type_dict(self, vari_hist:dict) -> dict:
        var_type_dict = {}
        for var_dict in vari_hist.values():
            for var, values in var_dict.items():
                if var in var_type_dict.keys(): continue
                for v in values:
                    try: v = eval(v)
                    except: pass
                    var_type = type(v).__name__
                    var_type_dict[var] = var_type
        return var_type_dict
    
    def get_same_type_var(self, var_name:str, var_type_dict:dict):
        var_type = var_type_dict[var_name]
        new_var_list = [v for v, v_type in var_type_dict.items() 
                        if v_type == var_type and v != var_name]
        return Randoms.choice(new_var_list) if new_var_list else None
    

    def residue_var_map(self):
        # Using same name str to map variables
        for b_var in self.b_var_name_list:
            for a_var in self.a_var_name_list:
                if b_var not in self.var_map.keys() and \
                    a_var not in self.var_map.values() and \
                    b_var == a_var:
                    self.var_map[b_var] = a_var

        # New variables
        for a_var in self.a_var_name_list:
            if a_var not in self.var_map.values():
                self.var_map[a_var] = a_var

        for b_var in self.b_var_name_list:
            if b_var not in self.var_map.keys():
                self.var_map[b_var] = b_var

    def run(self, a_tree, a_var_hist:dict, b_tree, b_var_hist:dict) -> dict:
        np_a = NodeParser()
        np_a.run(a_tree)
        self.a_var_name_list = np_a.var_name_list
        np_b = NodeParser()
        np_b.run(b_tree)
        self.b_var_name_list = np_b.var_name_list

        self.a_var_hist = a_var_hist
        self.b_var_hist = b_var_hist

        self.dea_var_map()
        self.type_var_map()
        self.lcs_var_map()
        self.residue_var_map()
        return self.var_map
    

    def tree_var_map(self, a_tree, b_tree):
        class GetVarList(ast.NodeVisitor):
            def __init__(self):
                self.var_dict = {}
                self.no = 0

            def visit(self, node):
                if isinstance(node, (ast.Name)):
                    self.var_dict[node] = (node.id, self.no)
                elif isinstance(node, ast.arg):
                    self.var_dict[node] = (node.arg, self.no)
                self.no += 1
                return self.generic_visit(node)
            
        gvl = GetVarList()
        gvl.visit(a_tree)
        a_var_dict = gvl.var_dict

        gvl = GetVarList()
        gvl.visit(b_tree)
        b_var_dict = gvl.var_dict

        var_map = {}
        for (b_var, b_num) in b_var_dict.values():
            node_map = {}
            for a_node, (a_var, a_num) in a_var_dict.items():
                dist = abs(b_num - a_num)
                node_map.setdefault(dist, []).append(a_node)
            if node_map:
                min_dist = min(list(node_map.keys()))
                min_node = Randoms.choice(node_map[min_dist])
                var_map[b_var] = a_var
                del a_var_dict[min_node]
        return var_map