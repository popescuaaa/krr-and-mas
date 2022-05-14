from base import Action
from typing import Dict

class AgentAction(Action):
    """
    Negotiation action made by an agent in the Commons Environment
    """
    def __init__(self, sender_id: int, resource_share: float = None,
                 consumption_adjustment: Dict[int, float] = None, no_action=False):
        """
        :param sender_id: The id of the agent sending the message
        :param resource_share: The proportion of the common resource that this agent wants to use
        :param consumption_adjustment: A dictionary of <agent_id, consumption_adjustment> pairs, where the
        consumption adjustment represents the amount by which the current agents **wants** that
        `agent_id' increase/decrease his resource_share
        :param no_action: A flag specifying that this agents does not wish to make any other adjustments (not to his
        resource_share, nor to the ones of other agents
        """
        self.sender_id = sender_id
        self.resource_share = resource_share
        self.consumption_adjustment = consumption_adjustment
        self.no_action = no_action

