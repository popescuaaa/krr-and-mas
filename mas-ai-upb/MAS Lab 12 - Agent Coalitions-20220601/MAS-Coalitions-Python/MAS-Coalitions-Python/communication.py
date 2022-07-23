from typing import Dict, List
from agents import CoalitionAgent
from base import Coalition

import logging.config
import yaml

with open('logging_conf.yaml', 'r') as f:
    log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)
logger = logging.getLogger("communication")


class CoalitionAction(object):
    DISBAND = "disband"
    REQUEST_JOIN = "request_join"
    ACCEPT_JOIN = "accept_join"
    DENY_JOIN = "deny_join"

    def __init__(self, action_type: str):
        self.type = action_type

class DisbandCoalition(CoalitionAction):
    def __init__(self, coalition: Coalition):
        super(DisbandCoalition, self).__init__(CoalitionAction.DISBAND)
        self.coalition = coalition


class RequestJoinCoalition(CoalitionAction):
    def __init__(self, sender: CoalitionAgent, receiver: CoalitionAgent,
                 coalition: Coalition, product_share: Dict[str, Dict[str, float]]):
        super(RequestJoinCoalition, self).__init__(CoalitionAction.REQUEST_JOIN)
        self.sender = sender
        self.receiver = receiver
        self.coalition = coalition
        self.product_share = product_share

        assert receiver == coalition.get_leader()


class AcceptJoinCoalition(CoalitionAction):
    def __init__(self, leader: CoalitionAgent, joining_agent: CoalitionAgent,
                 product_share: Dict[str, Dict[str, float]]):
        super(AcceptJoinCoalition, self).__init__(CoalitionAction.ACCEPT_JOIN)
        self.leader = leader
        self.joining_agent = joining_agent
        self.product_share = product_share


class DenyJoinCoalition(CoalitionAction):
    def __init__(self, leader: CoalitionAgent, pretender_agent: CoalitionAgent,
                 revised_share: Dict[str, Dict[str, float]]):
        super(DenyJoinCoalition, self).__init__(CoalitionAction.DENY_JOIN)
        self.leader = leader
        self.pretender = pretender_agent
        self.revised_share = revised_share

