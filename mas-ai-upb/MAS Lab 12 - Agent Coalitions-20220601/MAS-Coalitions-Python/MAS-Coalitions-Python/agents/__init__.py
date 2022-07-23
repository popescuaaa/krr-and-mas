from typing import List, Dict, Any
from base import Product

class Agent(object):
    """
    Base class to be implemented by agent implementations.
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



"""
#### AGENT PARENT CLASSES
"""
class CoalitionAgent(Agent):
    """
    Parent class for buyer agents that are part of a coalition
    """
    def __init__(self, name: str, resources: float, products: List[Product]):
        """
        Default constructor for CoalitionAgent
        """
        super(CoalitionAgent, self).__init__(name)
        self.resources = resources
        self.products = products

    def create_single_coalition(self) -> "Coalition":
        """
        Create coalition with single agent. Provide a desired distribution of agent resources and obtained value
        over the 2 product types (R1 and R2)
        :return: the Coalition containing the single agent
        """
        raise NotImplementedError("Must be implemented by student")

    def state_announced(self, agents: List["CoalitionAgent"], coalitions: List["Coalition"]) -> None:
        """
        Function called when a change in the set of coalitions is announced.
        :param agents:
        :param coalitions:
        :return:
        """
        pass

    def do_actions(self, messages: List["CoalitionAction"] = None) -> List["CoalitionAction"]:
        """
        Return a list of actions that the agent wants to perform during his turn. The actions include:
          - REQUEST to join a coalition
          - DISBAND a coalition - a coalition member disbands the
          - ACCEPT join request (a coalition leader accepts the join of a new member)
          - DENY join request (a coalition leader will deny the join request of a new
          member if it is not satisfied with the proposed agent share - contribution per product type
          + expected value return. In that case, it has to propose a counter offer, i.e. the inte)
        :param messages:
        :return:
        """
        raise NotImplementedError("Must be implemented by student")
