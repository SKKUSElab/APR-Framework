import ast

from .nodeParser import NodeParser

class NodeMap:

    @classmethod
    def get_line_node_map(cls, tree:ast) -> dict:
        np = NodeParser()
        np.run(tree=tree)
        return np.line_node_map
    
    @classmethod
    def get_trace_node_map(cls, tree:ast, traces:list) -> dict:
        line_node_map = cls.get_line_node_map(tree=tree)
        trace_node_map = {line_node_map[lineno]:line_node_map[lineno].__class__.__name__ 
                            for lineno in traces 
                            if lineno in line_node_map.keys()}
        return trace_node_map


    @classmethod
    def rep_node_map(cls, a_trace_node_map:dict, b_trace_node_map:dict) -> dict:
        rep_node_map = {}
        a_trace_node_map = dict(reversed(list(a_trace_node_map.items())))
        b_trace_node_map = dict(reversed(list(b_trace_node_map.items())))
        a_nodes = list(a_trace_node_map.keys())
        a_node_names = list(a_trace_node_map.values())
        b_nodes = list(b_trace_node_map.keys())
        b_node_names = list(b_trace_node_map.values())
        
        # Initialize a 2D array to store the lengths of LCS
        dp = [[0] * (len(b_node_names) + 1) for _ in range(len(a_node_names) + 1)]

        # Calculate the dp array
        for i in range(1, len(a_node_names) + 1):
            for j in range(1, len(b_node_names) + 1):
                if a_node_names[i - 1] == b_node_names[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # Node mapping with LCS
        # Crossover: rep Node Mapping
        i, j = len(a_node_names), len(b_node_names)
        while i > 0 and j > 0:
            if a_node_names[i - 1] == b_node_names[j - 1]:
                a_node = a_nodes[i - 1]
                b_node = b_nodes[j - 1]
                rep_node_map[a_node] = ('rep', b_node)
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
    
        return rep_node_map
    
    @classmethod
    def ins_node_map(cls, a_trace_node_map:dict, b_trace_node_map:dict, node_map:dict) -> dict:
        ins_node_map = {}
        a_node_list = list(a_trace_node_map.keys())
        b_node_list = list(b_trace_node_map.keys())
        for b, b_node in enumerate(b_node_list):
            ### Skip if it already mapped
            if ('rep', b_node) in node_map.values() or b == 0: continue
            for i in range(b, 0, -1):
                before_b_node = b_node_list[b-1]
                ### Find before_b_node's mapped a_node
                a_node = cls.find_ins_loc(a_node_list, before_b_node, node_map)
                if a_node is not None:
                    ### Inserts b_node before a_node 
                    ### in the next sequence of mapped before_a_node
                    if a_node not in ins_node_map.keys():
                        ins_node_map[a_node] = ('ins', b_node)
                    break
        return ins_node_map
    
    @classmethod
    def find_ins_loc(cls, a_node_list, before_b_node, node_map):
        for mapped_a_node, (_, mapped_b_node) in node_map.items():
            if before_b_node == mapped_b_node:
                before_a_node = mapped_a_node
                a_idx = a_node_list.index(before_a_node)
                if len(a_node_list) <= a_idx+1: break
                return a_node_list[a_idx+1]
        return None
    
    @classmethod
    def del_node_map(cls, a_trace_node_map:dict, node_map:dict) -> dict:
        del_node_map = {}
        a_node_list = list(a_trace_node_map.keys())
        for a_node in a_node_list:
            if a_node in node_map.keys(): continue
            del_node_map[a_node] = ('del', None)
        return del_node_map


    @classmethod
    def unify_node_map(cls, a_node_map:dict, b_node_map:dict) -> dict:
        for key, (ins, value) in b_node_map.items():
            if key in a_node_map.keys():
                a_node_map[key] = ('rep', value)
            else:
                a_node_map[key] = (ins, value)
        return a_node_map


    @classmethod
    def trace(cls, a_code:str, a_traces:list, b_code:str,  b_traces:list) -> dict:
        a_trace_node_map = cls.get_trace_node_map(ast.parse(a_code), a_traces)
        b_trace_node_map = cls.get_trace_node_map(ast.parse(b_code), b_traces)

        trace_map = cls.rep_node_map(a_trace_node_map, b_trace_node_map)
        return trace_map

    @classmethod
    def crossover(cls, a_tree:ast, a_traces:list, b_tree:ast,  b_traces:list) -> dict:
        a_trace_node_map = cls.get_trace_node_map(a_tree, a_traces)
        b_trace_node_map = cls.get_trace_node_map(b_tree, b_traces)

        # Node Mapping
        node_map = cls.rep_node_map(a_trace_node_map, b_trace_node_map)
        return node_map
    
    @classmethod
    def mutation(cls, a_tree:ast, a_traces:list, b_tree:ast,  b_traces:list) -> dict:
        node_map = {}
        a_trace_node_map = cls.get_trace_node_map(a_tree, a_traces)
        b_trace_node_map = cls.get_trace_node_map(b_tree, b_traces)

        # Node Mapping
        rep_node_map = cls.rep_node_map(a_trace_node_map, b_trace_node_map)
        del_node_map = cls.del_node_map(a_trace_node_map, rep_node_map)
        ins_node_map = cls.ins_node_map(a_trace_node_map, b_trace_node_map, rep_node_map)

        node_map = cls.unify_node_map(del_node_map, ins_node_map)
        return node_map
    