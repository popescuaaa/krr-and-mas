from Expression import Expr, Proposition
from typing import List
from Tree2 import Tree
from operators import Not, And, Implies, Equivalent, Or
from copy import deepcopy

SATISFIABLE = 'satisfiable'
NON_SATISFIABLE = 'non_satisfiable'


def has_conflict(leaves: Tree):
    conflict = False
    for i in range(len(leaves.data) - 1):
        for j in range(len(leaves.data)):
            if j != i:
                if isinstance(leaves.data[i], Proposition) and \
                        isinstance(leaves.data[j], Proposition) and \
                        leaves.data[i].is_negation_of(leaves.data[j]):
                    return True

    return conflict


def expand(node: Tree):
    if len(node.getChildren()) == 0:
        props = list(filter(lambda x: isinstance(x, Proposition), node.data))
        if len(props) == len(node.data):
            return

        for e in node.data:
            if isinstance(e, Or):
                node.data.remove(e)
                node.addChildren([
                    Tree(data=(node.data +
                               [e.left_expr])
                         ),
                    Tree(data=(node.data +
                               [e.right_expr])
                         )
                ])

            elif isinstance(e, Proposition):
                node.data.remove(e)
                node.data.append(e.simplify())

            elif isinstance(e, And):
                node.data.remove(e)
                node.data.append(e.left_expr)
                node.data.append(e.right_expr)

            else:
                node.data.remove(e)
                node.data.append(e.simplify())


class SemanticTableaux:
    def __init__(self, expressions: List[Expr]):
        self.expressions = expressions
        self.result = NON_SATISFIABLE
        self.example = []  # example of values which can be a solution
        self.unresolved = deepcopy(expressions)

        self.root = Tree(data=expressions)  # root
        self.build()

    def build(self) -> None:
        expansion_queue = [self.root]
        expansion_list = [self.root]

        while len(expansion_queue):
            current = expansion_queue.pop()
            expand(current)
            for c in current.getChildren():
                if c not in expansion_list:
                    expansion_list.append(c)
                    expansion_queue.append(c)

        self.root.prettyTree()

    def get_result(self):
        leaves = []
        queue = [self.root]
        explored = [self.root]

        while len(queue):
            current = queue.pop()
            if len(current.getChildren()) == 0:
                leaves.append(current)
            else:
                for c in current.getChildren():
                    if c not in explored:
                        explored.append(c)
                        queue.append(c)

        ok_leaves = []
        for c in leaves:
            if has_conflict(c):
                continue
            else:
                ok_leaves.append(c)
                self.example.append(c.data)

        if len(ok_leaves) == 0:
            return NON_SATISFIABLE, self.example
        else:
            return SATISFIABLE, self.example
