class Action(object):
    """
    Base class to be implemented by classes representing actions.
    """
    pass

class Perception(object):
    """
    Base class to be implemented by classes representing the totality of an agent's perceptions at a point in time.
    """
    pass


class Agent(object):
    """
    Base class to be implemented by agent implementations. A reactive agent is only defined by its Agent @ to
    perceptions.
    """

    def response(self, perceptions):
        """
        Computes the response of the agent to the perceptions. The perceptions are offered by the environment and the
        action is executed by the environment.

        :param perceptions: the perceptions that are given by the environment to the agent.
        :return: an {@link Action} to be executed by the agent on the environment.
        """
        raise NotImplementedError("Missing a response")

    def __str__(self):
        """
        :return: override to return a 1-character string that encodes the agent name
        """
        return "A"


class AgentData(object):
    """
    The class contains data that characterizes the external state of an agent, from the point of view of the
    environment. For instance, the agent's position.
    """
    def __init__(self, linked_agent):
        """
        :param linked_agent: the internal implementation of the agent about which this
        instance contains environment data.
        """
        self.linked_agent = linked_agent


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.linked_agent == other.linked_agent
        else:
            return False
