from typing import Callable, List

from commons import CommonsAgent, CommonsPerception
from communication import AgentAction


class ASoriciAgent(CommonsAgent):
    def __init__(self, agent_id):
        super(ASoriciAgent, self).__init__(agent_id)

    def specify_share(self, perception: CommonsPerception) -> float:
        return 1.0 / (2 * perception.num_agents)

    def negotiation_response(self, negotiation_round: int, perception: CommonsPerception,
                             utility_func: Callable[[float, float, List[float]], float]) -> AgentAction:
        return AgentAction(self.id, resource_share=1.0 / (2 * perception.num_agents),
                           no_action=True)


