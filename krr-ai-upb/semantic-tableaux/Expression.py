class Expr:
    """
    Empty base class defining an expression in propositional logic.
    Propositions and operators that build expressions will extend from this class.
    """

    def negate(self) -> "Expr":
        raise NotImplementedError("Method not implemented")

    def eval(self) -> bool:
        raise NotImplementedError("Method not implemented")

    def simplify(self) -> "Expr":
        """
        The simplify method operates in two ways:
          1. it converts "->" and "<->" to expressions containing only AND, OR, NOT operators
          2. it eliminates the NOT operator from expressions, until it reaches propositions
        """
        return self


class Proposition(Expr):
    """
    Defines a term in propositional logic
    """

    def __init__(self, name: str, value: bool):
        self.name = name
        self.value = value

    def negate(self):
        return Proposition(self.name, not self.value)

    def eval(self):
        return self.value

    def is_negation_of(self, other: "Proposition"):
        return self == other.negate()

    def __hash__(self) -> int:
        name_hash = hash(self.name)
        if self.value:
            return name_hash + 1
        else:
            return name_hash

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def __str__(self):
        if self.value:
            return self.name
        else:
            return "¬" + self.name

    def __repr__(self):
        return self.__str__()