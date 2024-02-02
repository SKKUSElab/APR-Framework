import ast
from collections import defaultdict, deque
from apted import APTED


class TED:
    class Tree(object):
        """Represents a Tree Node"""

        def __init__(self, name, *children):
            self.name = name
            self.children = list(children)

        def bracket(self):
            """Show tree using brackets notation"""
            result = str(self.name)
            for child in self.children:
                result += child.bracket()
            return "{{{}}}".format(result)

        def __repr__(self):
            return self.bracket()

        @classmethod
        def from_text(cls, text):
            """Create tree from bracket notation
            Bracket notation encodes the trees with nested parentheses, for example,
            in tree {A{B{X}{Y}{F}}{C}} the root node has label A and two children
            with labels B and C. Node with label B has three children with labels
            X, Y, F.
            """
            tree_stack = []
            stack = []
            for letter in text:
                if letter == "{":
                    stack.append("")
                elif letter == "}":
                    text = stack.pop()
                    children = deque()
                    while tree_stack and tree_stack[-1][1] > len(stack):
                        child, _ = tree_stack.pop()
                        children.appendleft(child)

                    tree_stack.append((cls(text, *children), len(stack)))
                else:
                    stack[-1] += letter
            return tree_stack[0][0]

    def dedupe_nodes(self, l):
        new_list = []
        ids_collected = []
        for i in l:
            if i["id"] not in ids_collected:
                new_list.append(i)
                ids_collected.append(i["id"])
        return new_list

    def node_properties(self, node):
        d = {}
        for field, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                d[field] = self.node_properties(value)
            elif (
                    isinstance(value, list) and len(value) > 0 and isinstance(value[0], ast.AST)
            ):
                d[field] = [self.node_properties(v) for v in value]
            else:
                d[field] = value
        return d

    def node_to_dict(self, node, parent):
        i = []
        children = list(ast.iter_child_nodes(node))
        if len(children) > 0:
            for n in children:
                i.extend(self.node_to_dict(n, node))

        d = self.node_properties(node)
        if hasattr(node, "lineno"):
            d["lineno"] = node.lineno
        i.append(
            {
                "id": id(node),
                "name": type(node).__name__,
                "parent": id(parent),
                "data": d,
            }
        )
        return i

    def bulidTree(self, codeTree):

        def tree():
            return defaultdict(tree)

        def add(t, keys):
            for key in keys:
                t = t[key]

        def dicts(t):
            # return {k: dicts(t[k]) for k in t}
            dic = {}
            for k in t:
                dic[k] = dicts(t[k])
            return dic

        def TreeText(t):
            text = {}
            for k in t:
                text[k] = TreeText(t[k])

            treeTxt = str(text).replace('{}', '').replace('\'', '').replace(':', '').replace(' ', '').replace(',', '}{')
            return text

        def tagName(cur_node):
            if cur_node['name'] == 'arg':
                return cur_node['data']['arg']
            elif cur_node['name'] == 'Name':
                return cur_node['data']['id']
            elif cur_node['name'] == 'Num':
                return cur_node['data']['n']
            elif cur_node['name'] == 'Attribute':
                return cur_node['data']['attr']
            else:
                return cur_node['name']

        parent_List = []
        for i in codeTree:  # 遍历找到root id
            parent_List.append(i['parent'])
        leafNode = []
        for i in codeTree:  # 遍历找到leaf id
            if i['id'] not in parent_List:
                leafNode.append(i)

        path_List = []
        test = tree()
        for i in leafNode:
            cur_node = i
            s = str(tagName(cur_node))
            for i in codeTree:
                if cur_node['parent'] == i['id']:
                    cur_node = i
                    r = tagName(cur_node)
                    s = str(r) + ',' + s
            path_List.append(s)
            add(test, s.split(','))
        tree = dicts(test)
        # pprint(tree)
        treeTxt = TreeText(test)
        treeTxt = str(treeTxt).replace('{}', '').replace('\'', '').replace(':', '').replace(' ', '').replace(',', '}{')
        # print(treeTxt)
        return treeTxt

    def preprocess_run(self, code1, code2):
        class VMTransformer(ast.NodeTransformer):
            def __init__(self):
                self.varis = []

            def visit_Name(self, node):
                if node.id in self.varis:
                    node.id = "var"
                self.generic_visit(node)
                return node

            def visit_arg(self, node):
                if node.arg in self.varis:
                    node.arg = "var"
                self.generic_visit(node)
                return node
            
            def run(self, code):
                varis = []
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                        varis.append(str(node.id))
                    elif isinstance(node, ast.arg):
                        varis.append(str(node.arg))
                self.varis = list(set(varis))
                tree = self.visit(tree)
                swt_code = ast.unparse(tree)
                return swt_code
        
        code1 = VMTransformer().run(code1)
        code2 = VMTransformer().run(code2)

        return self.run(code1, code2)

    def run(self, code1, code2):
        tree1 = ast.parse(code1)
        nodeDict1 = self.node_to_dict(tree1, None)
        data1 = self.dedupe_nodes(nodeDict1)
        tree1 = self.bulidTree(data1)

        tree2 = ast.parse(code2)
        nodeDict2 = self.node_to_dict(tree2, None)
        data2 = self.dedupe_nodes(nodeDict2)
        tree2 = self.bulidTree(data2)

        tree1, tree2 = map(self.Tree.from_text, (tree1, tree2))
        apted = APTED(tree1, tree2)
        ted = apted.compute_edit_distance()
        return ted

# '''Test Code'''
# code1 = """def func(v, v):
#     for v in range(len(v)):
#         if v <= v[v]:
#             return v
#     return len(v)"""
# code2 = """def search(x, seq):
#     length = len(seq)
#     if x < seq[0]:
#         return 0
#     elif x > seq[length -1]:
#         return length
#     for v in range(len(seq)):
#         if x <= seq[v]:
#             return v"""
# ted = TED().run(code1, code2)
# print("Tree Edit Distance: ", ted)


'''Diff Test Code'''
# diff = difflib.unified_diff(code1.splitlines(keepends=True), code2.splitlines(keepends=True))
# res = ''.join(diff)
# print(res)