from typing import List, Dict, Any

from agents import CoalitionAgent
from base import Coalition, Product
from communication import CoalitionAction, DenyJoinCoalition, AcceptJoinCoalition, RequestJoinCoalition


class MyCoalitionAgent(CoalitionAgent):
    PROD_TYPE_R1 = "r1"
    PROD_TYPE_R2 = "r2"

    def __init__(self, name: str, resources: float, products: List[Product]):
        super(MyCoalitionAgent, self).__init__(name, resources, products)
        self.coalitions = None
        self.coalition = None
        self.share = None

    def create_single_coalition(self) -> Coalition:
        c = Coalition(self.products)

        r1_product = min(self.products, key=lambda product: product.price)
        r1_shares = self.resources / r1_product.price * r1_product.value

        c.set_agent(self, share={self.PROD_TYPE_R1:
            {
                Coalition.PROD_CONTRIB: self.resources,
                Coalition.PROD_VALUE: r1_shares
            }
        })
        return c

    def state_announced(self, agents: List[CoalitionAgent], coalitions: List[Coalition]) -> None:
        # Find the best coalition in the current state of the env
        super().state_announced(agents, coalitions)
        self.coalitions = coalitions  # Get current coalitions

        for coalition in coalitions:
            if coalition.is_member(self):
                self.coalition = coalition
                members = self.coalition.member_data
                for member in members:
                    if member[Coalition.MEMBER].name == self.name:
                        self.share = member[Coalition.SHARE]
                break

    def do_actions(self, messages: List[CoalitionAction] = None) -> List[CoalitionAction]:
        accept_join = False
        request_join = False
        actions = []
        collection = []

        for message in messages:
            if message.type == CoalitionAction.REQUEST_JOIN:
                collection.append(message.coalition)
                if self.coalition.get_leader() != self:
                    continue  # Not in mine
                else:
                    actions.append(AcceptJoinCoalition(self, message.sender, message.product_share))
            elif message.type == CoalitionAction.ACCEPT_JOIN:
                actions.append(AcceptJoinCoalition(self, message.sender, message.share))
            elif message.type == CoalitionAction.DENY_JOIN:
                continue
            elif message.type == CoalitionAction.DISBAND:
                actions.append(RequestJoinCoalition(self, message.sender, collection[-1], message.product_share))

        return actions
