from abc import ABC
from Expression import Expr


class Operator(ABC):
    """
    A class necessary for internal use.
    """
    pass


class UnaryOperator(Expr, Operator, ABC):
    """
    Base class for a unary operator in propositional logic
    """

    def __init__(self, op_name: str, expression: Expr):
        self.op_name = op_name
        self.expression = expression

    def __str__(self):
        return "%s(%s)" % (self.op_name.upper(), str(self.expression))

    def __repr__(self):
        return self.__str__()


class Not(UnaryOperator):
    """
    Defines a negation operation in propositional logic
    """

    def __init__(self, expression):
        super(Not, self).__init__("NOT", expression)

    def negate(self):
        return self.expression

    def eval(self):
        return not self.expression.eval()

    def simplify(self):
        """
        Simplification for a NOT operator is pushing the negation inside the expression
        :return: The propositional logic expression resulting from pushing the negation operator inside the negated
        expression (i.e. removal of the negation operator)
        """
        return self.expression.negate()


class BinaryOperator(Expr, Operator, ABC):
    """
    Base class for a binary operator in propositional logic
    """

    def __init__(self, op_name: str, left_expr: Expr, right_expr: Expr):
        self.name = op_name
        self.left_expr = left_expr
        self.right_expr = right_expr

    def __str__(self):
        return "%s(%s, %s)" % (self.name.upper(), str(self.left_expr), str(self.right_expr))

    def __repr__(self):
        return self.__str__()


class And(BinaryOperator):
    """
    Defines an "AND" operator in propositional logic
    """

    def __init__(self, left_expr: Expr, right_expr: Expr):
        super(And, self).__init__("AND", left_expr, right_expr)

    def eval(self):
        left_expr_eval = self.left_expr.eval()
        if not left_expr_eval:
            return False
        else:
            return self.right_expr.eval()

    def negate(self):
        return Or(self.left_expr.negate(), self.right_expr.negate())

    def simplify(self):
        return And(self.left_expr.simplify(), self.right_expr.simplify())


class Or(BinaryOperator):
    """
    Defines an "OR" operator in propositional logic
    """

    def __init__(self, left_expr: Expr, right_expr: Expr):
        super(Or, self).__init__("OR", left_expr, right_expr)

    def eval(self):
        left_expr_eval = self.left_expr.eval()
        if left_expr_eval:
            return True
        else:
            return self.right_expr.eval()

    def negate(self):
        return And(self.left_expr.negate(), self.right_expr.negate())

    def simplify(self):
        return Or(self.left_expr.simplify(), self.right_expr.simplify())


class Implies(BinaryOperator):
    """
    Defines an "Implication" operator in propositional logic
    """

    def __init__(self, left_expr: Expr, right_expr: Expr):
        super(Implies, self).__init__("IMPL", left_expr, right_expr)

    def eval(self):
        return self.simplify().eval()

    def negate(self):
        return And(self.left_expr, self.right_expr.negate())

    def simplify(self):
        return Or(self.left_expr.negate(), self.right_expr)


class Equivalent(BinaryOperator):
    """
    Defines an "Equivalence" operator in propositional logic
    """

    def __init__(self, left_expr: Expr, right_expr: Expr):
        super(Equivalent, self).__init__("EQ", left_expr, right_expr)

    def eval(self):
        return self.simplify().eval()

    def negate(self):
        return Or(And(self.left_expr, self.right_expr.negate()), And(self.left_expr.negate(), self.right_expr))

    def simplify(self):
        return Or(And(self.left_expr, self.right_expr), And(self.left_expr.negate(), self.right_expr.negate()))
