from Expression import Expr, Proposition
from typing import List
from Tree import TreeNode
from operators import Not, And, Implies, Equivalent, Or
from copy import deepcopy

SATISFIABLE = 'satisfiable'
NON_SATISFIABLE = 'non_satisfiable'


class SemanticTableaux:
    def __init__(self, expressions: List[Expr]):
        self.expressions = expressions
        self.result = NON_SATISFIABLE
        self.example = None  # example of values which can be a solution
        self.unresolved = deepcopy(expressions)

        self.root = TreeNode(value=expressions, parent=None)  # root
        self.build()

    def build(self) -> None:
        if self.result == SATISFIABLE:
            return

        # Trunks
        for expr in self.unresolved:
            if isinstance(expr, And):
                self.unresolved.remove(expr)  # remove and move values to next instance of root
                self.root = TreeNode(parent=self.root,
                                     value=([_expr for _expr in self.unresolved] +
                                            [expr.left_expr, expr.right_expr]))

        # Negation and parenthesis
        for expr in self.unresolved:
            if isinstance(expr, Not):
                print(expr)
                self.unresolved.remove(expr)  # remove and move values to next instance of root

                # Value
                if isinstance(expr.expression, Proposition):
                    self.root = TreeNode(parent=self.root,
                                         value=([_expr for _expr in self.unresolved] +
                                                [expr.expression.negate()]))

                # Trunk
                elif isinstance(expr.expression, Or):
                    self.root = TreeNode(parent=self.root,
                                         value=([_expr for _expr in self.unresolved] +
                                                [expr.expression.left_expr.negate(),
                                                 expr.expression.right_expr.negate()]))

                # Sub-branching with negation
                elif isinstance(expr.expression, Implies):
                    self.root = TreeNode(parent=self.root,
                                         value=([_expr for _expr in self.unresolved] +
                                                [expr.expression.left_expr,
                                                 expr.expression.right_expr.negate()]))

                elif isinstance(expr.expression, Equivalent):
                    self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                              [And(expr.expression.left_expr, expr.expression.right_expr.negate())]),
                                       target=self.root)
                    self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                              [And(expr.expression.left_expr.negate(), expr.expression.right_expr)]),
                                       target=self.root)

                elif isinstance(expr.expression, And):
                    self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                              [expr.expression.left_expr.negate()]),
                                       target=self.root)
                    self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                              [expr.expression.right_expr.negate()]),
                                       target=self.root)

        # Branching and checking
        for expr in self.unresolved:
            if isinstance(expr, Proposition):
                continue

            elif isinstance(expr, Or):
                self.unresolved.remove(expr)
                self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                          [expr.left_expr]),
                                   target=self.root)
                self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                          [expr.right_expr]),
                                   target=self.root)

            # Sub-branching with negation
            elif isinstance(expr, Implies):
                self.unresolved.remove(expr)
                self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                          [expr.left_expr.negate()]),
                                   target=self.root)
                self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                          [expr.right_expr]),
                                   target=self.root)

            elif isinstance(expr, Equivalent):
                self.unresolved.remove(expr)
                self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                          [And(expr.left_expr, expr.right_expr)]),
                                   target=self.root)
                self.root.add_node(value=([_expr for _expr in self.unresolved] +
                                          [And(expr.left_expr.negate(), expr.right_expr.negate())]),
                                   target=self.root)
