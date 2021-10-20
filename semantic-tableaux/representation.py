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

    # Test 1:
    # expr1 = Implies(Proposition("p", True), Proposition("q", True))
    # expr2 = Implies(Proposition("q", True), Proposition("r", True))
    # # expr3 = And(Proposition("p", True), Proposition("r", False))
    # expr3 = Not(Implies(Proposition("p", True), Proposition("r", True)))

    # Test 2:
    """
        1. IF weather is sunny THEN park is beautiful. 
        2. IF park is beautiful THEN people walk dogs. 
        3. IF people walk dogs THEN park full of dogs. 
        4. Weather is sunny AND NOT park full of dogs.
        
    """
    expr1 = Implies(Proposition("s", True), Proposition("p", True))
    expr2 = Implies(Proposition("p", True), Proposition("d", True))
    expr3 = Implies(Proposition("d", True), Proposition("pfd", False))
    expr4 = And(Proposition("s", True), Proposition("pfd", False))

    # semantic_tableaux = SemanticTableaux([expr1, expr2, expr3, expr4])
    # print(semantic_tableaux.get_result())

    # Test 3:
    """
        1. IF Paul likes apples THEN Paul buys apples.
        2. IF Wendy likes apples THEN Wendy buys apples.
        3. IF Susan likes apples THEN Susan buys apples.
        4. IF Wendy buys apples THEN basket has apples.
        5. Paul likes apples OR Wendy likes apples OR Susan likes apples. 
        6. Basket has apples.

    """
    expr1 = Implies(Proposition("pla", True), Proposition("pba", True))
    expr2 = Implies(Proposition("wla", True), Proposition("wba", True))
    expr3 = Implies(Proposition("sla", True), Proposition("sba", True))
    expr4 = Implies(Proposition("wba", True), Proposition("bha", True))
    expr5 = Or(Or(Proposition("pla", True), Proposition("wba", True)), Proposition("sla", True))
    expr6 = Proposition("bha", True)

    # semantic_tableaux = SemanticTableaux([expr1, expr2, expr3, expr4, expr5, expr6])
    # print(semantic_tableaux.get_result())

    # Test 3
    """
        1. IF Yueh is blackmailed THEN Yueh pacts with Harkonen. 
        2. IF Yueh pacts with Harkonen THEN NOT Yueh is loyal. 
        3. Duke Atreides rewards Yueh IFF Yueh is loyal.
        4. Yueh is blackmailed AND Duke Atreides rewards Yueh.
    """
    expr1 = Implies(Proposition("y", True), Proposition("yph", True))
    expr2 = Implies(Proposition("yph", True), Proposition("yl", False))
    expr3 = Equivalent(Proposition("dary", True), Proposition("yl", True))
    expr4 = And(Proposition("y", True), Proposition("dary", True))

    semantic_tableaux = SemanticTableaux([expr1, expr2, expr3, expr4])
    print(semantic_tableaux.get_result())

    # Test 4:
    """
        1. Alfred takes car OR Alfred takes bus.
        2. Car goes work IFF car has gas.
        3. Alfred goes work IFF Alfred takes car AND car goes work. 
        4. Alfred goes work IFF Alfred takes bus AND bus goes work. 
        5. Alfred takes bus IFF NOT car goes work.
        6. Alfred takes car IFF car has gas.
        7. Bus goes work IFF NOT city has traffic.
        8. NOT car has gas.
        9. City has traffic.
        10. Alfred goes work.

    """

    expr1 = Or(Proposition("ac", True), Proposition("ab", True))
    expr2 = Equivalent(Proposition("cgw", True), Proposition("chg", True))
    expr3 = Equivalent(Proposition("agw", True), And(Proposition("ac", True), Proposition("chw", True)))
    expr4 = Equivalent(Proposition("agw", True), And(Proposition("ab", True), Proposition("bgw", True)))
    expr5 = Equivalent(Proposition("ab", True), Proposition("cgw", False))
    expr6 = Equivalent(Proposition("ac", True), Proposition("chg", True))
    expr7 = Equivalent(Proposition("bgw", True), Proposition("cht", False))
    expr8 = Proposition("chg", False)
    expr9 = Proposition("cht", True)
    expr10 = Proposition("agw", True)

    # semantic_tableaux = SemanticTableaux([expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10])
    # print(semantic_tableaux.get_result())
