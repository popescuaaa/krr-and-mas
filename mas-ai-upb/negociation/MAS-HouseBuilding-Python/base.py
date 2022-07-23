class Agent(object):
    """
    Base class to be implemented by agent implementations. A reactive agent is only defined by its Agent @ to
    perceptions.
    """
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        """
        Two agents are equal if their names are the same
        :param other: the other agent
        :return: True if the `other' agent has the same name as this one
        """
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return "%s" % self.name


class Environment(object):
    """
    Base class to be implemented by environment implementations.
    """

    def goals_completed(self):
        """
        :return: return True if the goals of all the agents have been completed
        """
        raise NotImplementedError("Method not implemented")

    def step(self):
        """
        When the method is invoked, all agents should receive a perception of the environment and decide on an
        action to perform.
        """
        raise NotImplementedError("Method not implemented")

    def __str__(self):
        raise NotImplementedError("Method not implemented")
