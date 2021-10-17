from Expression import Proposition
from semantic_tableaux import SemanticTableaux
from operators import *

if __name__ == "__main__":
    a1 = Proposition("A1", True)
    neg_a1 = Proposition("A1", False)

    a2 = Proposition("A2", True)
    a3 = Proposition("A3", True)

    assert a1.is_negation_of(neg_a1)
    assert neg_a1.is_negation_of(a1)

    assert a2 != a3
    assert a1 == neg_a1.negate()

    expr1 = Implies(a1, a2)
    expr2 = Or(a3, Not(Or(a3, neg_a1)))

    assert expr1.eval(), "a1->a2 must be true, since a1 and a2 are true"
    assert expr2.eval(), "a3 v ~(a3 v ~a1) must be true, since a3 is true"

    expr = Not(And(expr1, expr2))
    # print("Truth value of %s is %r" % (str(expr), expr.eval()))
    #
    # print("Simplified version of expression \n\t%s is \n\t%s" % (str(expr), str(expr.simplify())))
    #
    # print("Negation of expression \n\t%s is \n\t%s" % (str(expr), str(expr.negate())))

    expr1 = Implies(Proposition("p", True), Proposition("q", True))
    expr2 = Implies(Proposition("q", True), Proposition("r", True))
    # expr3 = And(Proposition("p", True), Proposition("r", False))
    expr3 = Not(Implies(Proposition("p", True), Proposition("r", True)))

    semantic_tableaux = SemanticTableaux([expr1, expr2, expr3])
