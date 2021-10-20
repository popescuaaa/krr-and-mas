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
                    Tree(data=([_expr for _expr in node.data] +
                               [e.left_expr])
                         ),
                    Tree(data=([_expr for _expr in node.data] +
                               [e.right_expr])
                         )
                ])

            elif isinstance(e, Implies):
                node.data.remove(e)
                node.addChildren([
                    Tree(data=([_expr for _expr in node.data] +
                               [e.left_expr.negate()])
                         ),
                    Tree(data=([_expr for _expr in node.data] +
                               [e.right_expr])
                         )
                ])

            elif isinstance(e, Equivalent):
                node.data.remove(e)
                node.addChildren([
                    Tree(data=([_expr for _expr in node.data] +
                               [And(e.left_expr, e.right_expr)])
                         ),
                    Tree(data=([_expr for _expr in node.data] +
                               [And(e.left_expr.negate(), e.right_expr.negate())])
                         )
                ])

            elif isinstance(e, And):
                node.data.remove(e)
                node.addChild(
                    Tree(data=([_expr for _expr in node.data] +
                               [e.left_expr, e.right_expr])
                         )
                )
            else:
                continue


class SemanticTableaux:
    def __init__(self, expressions: List[Expr]):
        self.expressions = expressions
        self.result = NON_SATISFIABLE
        self.example = None  # example of values which can be a solution
        self.unresolved = deepcopy(expressions)

        self.root = Tree(data=expressions)  # root
        self.build()

    def build(self) -> None:
        # Trunks
        for expr in self.root.data:
            if isinstance(expr, And):
                self.root.data.remove(expr)
                self.root.addChild(
                    Tree(data=([_expr for _expr in self.root.data] +
                               [expr.left_expr, expr.right_expr]))
                )

        # Negation and parenthesis
        for expr in self.root.data:
            if isinstance(expr, Not):

                if isinstance(expr.expression, Proposition):
                    # self.root.data.remove(expr)
                    # self.root.addChild(
                    #     Tree(data=([_expr for _expr in self.root.data] +
                    #                [expr.expression.negate()]))
                    # )
                    continue

                # Trunk
                elif isinstance(expr.expression, Or):
                    self.root.data.remove(expr)
                    self.root.addChild(
                        Tree(data=([_expr for _expr in self.root.data] +
                                   [expr.expression.left_expr.negate(),
                                    expr.expression.right_expr.negate()])
                             )
                    )

                # Sub-branching with negation
                elif isinstance(expr.expression, Implies):
                    self.root.data.remove(expr)
                    self.root.addChild(
                        Tree(data=([_expr for _expr in self.root.data] +
                                   [expr.expression.left_expr,
                                    expr.expression.right_expr.negate()])
                             )
                    )

                elif isinstance(expr.expression, Equivalent):
                    self.root.data.remove(expr)
                    self.root.addChildren([
                        Tree(data=([_expr for _expr in self.root.data] +
                                   [And(expr.expression.left_expr, expr.expression.right_expr.negate())])
                             ),
                        Tree(data=([_expr for _expr in self.root.data] +
                                   [And(expr.expression.left_expr.negate(), expr.expression.right_expr)])
                             )
                    ])

                elif isinstance(expr.expression, And):
                    self.root.data.remove(expr)
                    self.root.addChildren([
                        Tree(data=([_expr for _expr in self.root.data] +
                                   [expr.expression.left_expr.negate()])
                             ),
                        Tree(data=([_expr for _expr in self.root.data] +
                                   [expr.expression.right_expr.negate()])
                             )
                    ])

                else:
                    continue

        # Branching and checking
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
            print(c)
            print(has_conflict(c))
            if has_conflict(c):
                continue
            else:
                ok_leaves.append(c)

        if len(ok_leaves) == 0:
            return NON_SATISFIABLE
        else:
            return SATISFIABLE
