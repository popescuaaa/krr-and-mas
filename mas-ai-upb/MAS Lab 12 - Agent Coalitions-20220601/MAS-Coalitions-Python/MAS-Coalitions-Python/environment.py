from base import Product, Coalition
from typing import List, Dict
import json
import yaml

from agents import CoalitionAgent
from agents.student_agent import MyCoalitionAgent
from communication import CoalitionAction

import logging.config

with open('logging_conf.yaml', 'r') as f:
    log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)
logger = logging.getLogger("environment")


"""
ENVIRONMENT IMPLEMENTATION
"""


class CoalitionEnvironment(object):
    MAX_ROUNDS = 20

    def __init__(self, agent_cfg_file: str, products_cfg_file: str):
        super(CoalitionEnvironment, self).__init__()

        self.agent_cfg_file = agent_cfg_file
        self.products_cfg_file = products_cfg_file

        self.agents: List[CoalitionAgent] = []
        self.products: List[Product] = []
        self.coalitions_dict: Dict[CoalitionAgent, Coalition] = {}

        self.round = 0


    def _get_agents_ordered(self):
        return sorted(self.agents, key=lambda a: a.resources, reverse=True)

    def initialize(self):
        """
        Initializes the coalition environment
        """
        agent_configs = None
        product_configs = None

        with open(self.agent_cfg_file) as f:
            agent_configs = json.load(f)

        with open(self.products_cfg_file) as f:
            product_configs = json.load(f)

        for prod_cfg in product_configs:
            self.products.append(Product(prod_cfg["product"]["type"],
                                         prod_cfg["product"]["value"],
                                         prod_cfg["product"]["price"]))

        for ag_cfg in agent_configs:
            self.agents.append(MyCoalitionAgent(ag_cfg["agent"]["name"],
                                                ag_cfg["agent"]["resources"], self.products))


    def _broadcast_state(self):
        for ag in self.agents:
            ag.state_announced(self.agents, list(self.coalitions_dict.values()))


    def run(self):
        message_box: Dict[CoalitionAgent, List[CoalitionAction]] \
            = dict([(ag, []) for ag in self.agents])

        # create initial, single agent coalitions and broadcast them
        for ag in self.agents:
            coalition = ag.create_single_coalition()
            self.coalitions_dict[ag] = coalition

        self._broadcast_state()

        config_changed = True
        self.round = 0

        while config_changed and self.round < CoalitionEnvironment.MAX_ROUNDS:
            config_changed = False
            self.round += 1

            # pass token to agents in order of decreasing resources
            for ag in self._get_agents_ordered():
                ag_messages = message_box[ag]
                agent_actions = ag.do_actions(messages=ag_messages)

                # clear the message box for an agent, after having sent existing messages
                message_box[ag].clear()

                for act in agent_actions:
                    if act.type == CoalitionAction.REQUEST_JOIN:
                        receiver = act.receiver
                        message_box[receiver].append(act)
                    elif act.type == CoalitionAction.DENY_JOIN:
                        assert ag == act.leader, \
                            "Agent denying a coalition: %s join should be its leader: %s" % (ag.name, act.leader.name)
                        message_box[act.pretender].append(act)
                    elif act.type == CoalitionAction.ACCEPT_JOIN:
                        assert ag == act.leader, \
                            "Agent accepting a coalition: %s join should be its leader: %s" % (ag.name, act.leader.name)
                        coalition = self.coalitions_dict[ag]
                        if coalition:
                            coalition.set_agent(act.joining_agent, act.product_share)
                            del self.coalitions_dict[ag]
                            del self.coalitions_dict[act.joining_agent]
                            self.coalitions_dict[coalition.get_leader()] = coalition

                            config_changed = True
                            self._broadcast_state()
                        else:
                            raise ValueError("Accepting to JOIN a coalition of agent %s "
                                             "for which there is no record" % ag.name)
                    elif act.type == CoalitionAction.DISBAND:
                        assert act.coalition.is_member(ag), "Agent %s attempting to disband coalition %s " \
                                                            "is not a member of it" % (ag.name, str(act.coalition))
                        leader = act.coalition.get_leader()
                        members = act.coalition.get_members()

                        del self.coalitions_dict[leader]
                        for ag in members:
                            self.coalitions_dict[ag] = ag.create_single_coalition()

                        config_changed = True
                        self._broadcast_state()
                    else:
                        raise ValueError("Unknown action type: %s" % act.type)

            print("[NOTIFICATION] END OF ROUND %i!" % self.round)
            print(self)


    def __str__(self):
        res = "#### Coalition Environment ####" + "\n"
        for c in self.coalitions_dict.values():
            res += str(c)
            res += "\n"
        return res


if __name__ == "__main__":
    env = CoalitionEnvironment(agent_cfg_file="agent_config_2.json", products_cfg_file="products_config.json")
    env.initialize()
    env.run()


