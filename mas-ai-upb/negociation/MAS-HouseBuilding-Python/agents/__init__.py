from base import Agent
from typing import List, Dict, Any

"""
#### AGENT PARENT CLASSES
"""
class HouseOwnerAgent(Agent):
    """
    Parent class for the agent that plays the role of house owner
    """
    def __init__(self, role: str, budget_list: List[Dict[str, Any]]):
        """
        Default constructor for HouseOwnerAgent
        """
        super(HouseOwnerAgent, self).__init__(self.__class__.__name__ + "_" + role)
        self.role = role
        self.budget_dict = HouseOwnerAgent.__build_budget_dict(budget_list)

    @staticmethod
    def __build_budget_dict(budget_list: List[Dict[str, Any]]) -> Dict[str, int]:
        budget_dict = {}
        for item in budget_list:
            budget_dict[item["name"]] = item["budget"]

        return budget_dict

    def propose_item_budget(self, auction_item: str, auction_round: int) -> float:
        """
        Function called during the auction phase, when the owner agent has to announce a new price for a new
        auction round.
        :param auction_item:
        :param auction_round:
        :return:
        """
        raise NotImplementedError("Must be implemented by student")

    def notify_auction_round_result(self, auction_item: str, auction_round: int, responding_agents: List[str]) -> None:
        """
        Function called when there were company agents that responded to the last announced auction priced
        :param auction_item:
        :param auction_round:
        :param responding_agents: list of agent names that responded to the auction price
        :return:
        """
        pass

    def provide_negotiation_offer(self, negotiation_item: str, partner_agent: str,
                              negotiation_round: int) -> float:
        """
        Function called during the negotiation stage when the owner agent is asked to provide a new offer in the
        negotiation.
        If the agent gives an offer that is greater or equal to the response of the partner agent
        from the previous round, the protocol end successfully.
        :param negotiation_item:
        :param partner_agent:
        :param negotiation_round:
        :return:
        """
        raise NotImplementedError("Must be implemented by student")

    def notify_partner_response(self, response_msg: "NegotiationMessage") -> None:
        """
        Function called to notify the owner of a response from a company agent, in response to his current offer within
        the negotiation
        :param response_msg:
        :return:
        """
        pass

    def notify_negotiation_winner(self, negotiation_item: str, winning_agent: str, winning_offer: float) -> None:
        """
        Function called to notify the owner of the outcome of a negotiation
        :param negotiation_item:
        :param winning_agent:
        :param winning_offer:
        :return:
        """
        raise NotImplementedError("Must be implemented by student")



class CompanyAgent(Agent):
    """
    Parent class for the agent that play the role of a builder company
    """
    def __init__(self, role: str, specialties: List[Dict[str, Any]]):
        """
        Default constructor for CompanyAgent
        """
        super(CompanyAgent, self).__init__(self.__class__.__name__ + "_" + role)
        self.role = role
        self.specialties = CompanyAgent.__build_specialties_dict(specialties)

    @staticmethod
    def __build_specialties_dict(specialties: List[Dict[str, Any]]) -> Dict[str, int]:
        specialties_dict = {}
        for spec in specialties:
            specialties_dict[spec["specialty"]] = spec["cost"]

        return specialties_dict

    def has_specialty(self, specialty: str):
        return specialty in self.specialties

    def decide_bid(self, auction_item: str, auction_round: int, item_budget: float) -> bool:
        raise NotImplementedError("Must be implemented by student")

    def notify_won_auction(self, auction_item: str, auction_round: int, num_selected: int) -> None:
        """
        Function called when the agent is notified that it was selected as a result of the auction process
        :param auction_item: auction item for which the agent was selected
        :param auction_round: round number of the auction
        :param num_selected: the total number of agents selected
        """
        pass

    def respond_to_offer(self, initiator_msg: "NegotiationMessage") -> float:
        """
        Function called when the company agent is supposed to respond with a counter offer within a negotiation.
        If the agent responds with a lower or equal value than the one offered, the protocol will end successfully.
        :param initiator_msg:
        :return:
        """
        raise NotImplementedError("Must be implemented by student")

    def notify_contract_assigned(self, construction_item: str, price: float) -> None:
        """
        Notify the company agent that a contract has been assigned to it
        :param construction_item:
        :param price:
        :return:
        """
        pass

    def notify_negotiation_lost(self, construction_item: str) -> None:
        """
        Notify the company agent that a its negotiation for a construction item has failed
        :param construction_item:
        :return:
        """
        pass

