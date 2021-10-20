from Expression import Expr, Proposition
from typing import List


class TreeNode:
    """
    Node class for tree representation
    """

    def __init__(self,
                 parent: 'TreeNode' or None,
                 value: List[Expr] or None):

        self.parent = parent
        self.left = None
        self.right = None
        self.value = value

    def has_conflict(self) -> bool:
        assert self.value is not None, 'Cannot perform check on None value'

        conflict = False

        for expr1 in self.value:
            for expr2 in self.value:
                if expr2 != expr1:
                    if isinstance(expr1, Proposition) and isinstance(expr2, Proposition):
                        if expr2.is_negation_of(expr1) or expr1.is_negation_of(expr2):
                            conflict = True
                            break
                        break

        return conflict

    def add_node(self, value: List[Expr] or None) -> bool:
        if self.right is None:
            self.right = TreeNode(parent=self, value=value)
            return True

        if self.left is None:
            self.left = TreeNode(parent=self, value=value)
            return True

        if self.left.add_node(value=value):
            return True

        if self.left.add_node(value=value):
            return True

        return False


def log(root: TreeNode or None):
    if root is not None:
        if root.value is not None:
            if root.parent is not None:
                print('{} -> {}'.format(root.parent.value, root.value))
            else:
                print('0 -> {}'.format(root.value))
        log(root.left)
        log(root.right)
