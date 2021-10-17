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

    @staticmethod
    def add_node(value: List[Expr] or None, target: 'TreeNode') -> bool:
        if target.left is None:
            target.left = TreeNode(parent=target, value=value)
            return True
        elif target.right is None:
            target.right = TreeNode(parent=target, value=value)
            return True

        if target.add_node(value=value, target=target.left):
            return True

        if target.add_node(value=value, target=target.right):
            return True

        return False


def log(root: TreeNode or None):
    if root is not None:
        if root.value is not None:
            print(root.value)
        log(root.left)
        log(root.right)
