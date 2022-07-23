from typing import List, Dict, Any

from scipy.stats._multivariate import special_ortho_group_frozen

from agents import HouseOwnerAgent, CompanyAgent
from communication import NegotiationMessage


class MyACMEAgent(HouseOwnerAgent):

    def __init__(self, role: str, budget_list: List[Dict[str, Any]]):
        super(MyACMEAgent, self).__init__(role, budget_list)
        self.budget_dict = {budget["name"]: budget["budget"] for budget in budget_list}
        self.proposals = {}
        self.winners = {}
        self.partner_offers = {}
        self.offers = {}

    def propose_item_budget(self, auction_item: str, auction_round: int) -> float:
        if auction_round == 0:
            # Save the proposal
            self.proposals[auction_round] = [(auction_item, self.budget_dict[auction_item] * 0.2)]
            return self.budget_dict[auction_item] * 0.4
        elif auction_round == 1:
            # Save the proposal
            self.proposals[auction_round] = [(auction_item, self.budget_dict[auction_item] * 0.5)]
            return self.budget_dict[auction_item] * 0.7
        else:
            if auction_round not in self.proposals:
                self.proposals[auction_round] = []
            self.proposals[auction_round].append((auction_item, self.budget_dict[auction_item] * 0.5))
            return self.budget_dict[auction_item]

    def notify_auction_round_result(self, auction_item: str, auction_round: int, responding_agents: List[str]):
        self.partner_offers[auction_round] = {agent: [] for agent in responding_agents}
        self.offers[auction_round] = {agent: [] for agent in responding_agents}

    def provide_negotiation_offer(self, negotiation_item: str, partner_agent: str, negotiation_round: int) -> float:
        best_offer = self.proposals[negotiation_round][-1][1]  # last one

        if negotiation_round == 0:
            min_price = self.proposals[negotiation_round][-2][1]
            # Something in between
            offer = min_price + (best_offer - min_price) / 2
        else:
            previous_offer = self.offers[negotiation_round - 1][partner_agent][-1]
            agent_offer = self.partner_offers[negotiation_round][partner_agent][-1]
            # Something in between
            offer = previous_offer + (agent_offer - previous_offer) / 2

        self.offers[negotiation_round][partner_agent].append(offer)
        return offer

    def notify_partner_response(self, response_msg: NegotiationMessage) -> None:
        self.partner_offers[response_msg.negotiation_round][response_msg.sender].append(response_msg.offer)

    def notify_negotiation_winner(self, negotiation_item: str, winning_agent: str, winning_offer: float) -> None:
        self.winners[negotiation_item] = (winning_agent, winning_offer)


class MyCompanyAgent(CompanyAgent):

    def __init__(self, role: str, specialties: List[Dict[str, Any]]):
        super(MyCompanyAgent, self).__init__(role, specialties)
        self.total_contracts = 0
        self.auctions = {speciality["specialty"]: [] for speciality in specialties}
        self.results = {}
        self.specialities = specialties
        self.previous_offer = None

    def decide_bid(self, auction_item: str, auction_round: int, item_budget: float) -> bool:
        max_i_can_give = self.specialties[auction_item]
        # if item_budget > 2 * max_i_can_give:
        #     return True
        # elif self.total_contracts < 1:
        #     if item_budget < max_i_can_give:
        #         return False
        #     else:
        #         return True
        # else:
        #     return False
        if item_budget >= max_i_can_give:
            return True
        else:
            return False

    def notify_won_auction(self, auction_item: str, auction_round: int, num_selected: int):
        self.auctions[auction_item] = (True, num_selected)

    def respond_to_offer(self, initiator_msg: NegotiationMessage) -> float:
        min_offer = self.specialties[initiator_msg.negotiation_item]
        if initiator_msg.round == 0:
            if initiator_msg.offer > min_offer:
                offer = initiator_msg.offer * 1.5
            else:
                offer = min_offer * 1.7

            self.previous_offer = offer
        else:
            if initiator_msg.offer > min_offer:
                # Something in between
                offer = self.previous_offer + (initiator_msg.offer - self.previous_offer) / 2
            else:
                offer = min_offer * 1.7

        return offer

    def notify_contract_assigned(self, construction_item: str, price: float) -> None:
        self.results[construction_item] = (True, price)
        self.total_contracts += 1

    def notify_negotiation_lost(self, construction_item: str) -> None:
        self.results[construction_item] = (False, 0)
