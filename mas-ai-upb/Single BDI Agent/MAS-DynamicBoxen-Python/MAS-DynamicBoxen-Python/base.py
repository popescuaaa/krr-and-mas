
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
    def __init__(self, name: str = None):
        if not name:
            self.name = "*A"
        else:
            self.name = name


    def response(self, perception: Perception) -> Action:
        """
        Supplies the agent with perceptions and demands one action from the agent. The environment also specifies if the
        previous action of the agent has succeeded or not.

        :param perception: the perceptions offered by the environment to the agent.
        :return: he agent output, containing the action to perform. Action should be of type
        {@link blocksworld.BlocksWorldAction.Type#NONE} if the agent is not performing an action now,
        but may perform more actions in the future.
        Action should be of type {@link blocksworld.BlocksWorldAction.Type#AGENT_COMPLETED} if the agent will not
        perform any more actions ever in the future.
        """
        raise NotImplementedError("Missing a response")


    def status_string(self):
        """
        :return: a string that is printed at every cycle to show the status of the agent.
        """
        return NotImplementedError("Missing a status string")


    def __str__(self):
        """
        :return: The agent name
        """
        return self.name


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name


    def __hash__(self):
        return hash(self.name)





class Environment(object):
    """
    Base class to be implemented by environment implementations.
    """


    def add_agent(self, agent: Agent, desires, placement):
        """
        Adds an agent to the environment. The environment places the agent in it, in the specified state.
        :param agent: the agent to add.
        :param desires: a representation of the desires of the agent.
        :param placement: the initial position of the agent.
        """
        raise NotImplementedError("Method not implemented")


    def step(self) -> bool:
        """
        When the method is invoked, all agents should receive a perception of the environment and decide on an action to
        perform.
        :return: True if all agents completed their goals
        """
        raise NotImplementedError("Method not implemented")

    def __str__(self):
        raise NotImplementedError("Method not implemented")
