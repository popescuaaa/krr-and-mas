from typing import Dict, List
from base import Agent
from agents import HouseOwnerAgent, CompanyAgent

import logging.config
import yaml

with open('logging_conf.yaml', 'r') as f:
    log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)
logger = logging.getLogger("communication")


class NegotiationMessage(object):
    """
    Class representing the content of a negotiation message
    """
    def __init__(self, sender_name: str, receiver_name: str, negotiation_item: str,
                 conversation_id: str, round: int, offer: float = 0):
        self.sender = sender_name
        self.receiver = receiver_name
        self.negotiation_item = negotiation_item
        self.conversation_id = conversation_id
        self.round = round
        self.offer = offer

    def __str__(self) -> str:
        return "[NegotiationMsg] from: %s, to: %s, " \
               "item: %s, conv_id: %s, round: %i, offer: %f" % (self.sender, self.receiver, self.negotiation_item,
                                                                self.conversation_id, self.round, self.offer)

    def set_offer(self, offer):
        self.offer = offer

    def create_reply(self):
        return NegotiationMessage(self.receiver, self.sender, self.negotiation_item,
                                  self.conversation_id, self.round)


class MonotonicConcessionNegotiation(object):
    """
    Class representing a negotiation interaction between two agents
    """

    def __init__(self, initiator_agent: HouseOwnerAgent, partner_agent: CompanyAgent, negotiation_item: str,
                 num_rounds: int):
        self.initiator: HouseOwnerAgent = initiator_agent
        self.partner: CompanyAgent = partner_agent
        self.negotiation_item = negotiation_item
        self.num_rounds = num_rounds
        self.conversation_id = "conv" + "_" + negotiation_item + "_" + initiator_agent.name + "_" + partner_agent.name

        self.failed = False
        self.initiator_offer: float = 0
        self.partner_offer: float = 0
        self.round = 0

        self.negotiation_history: Dict[Agent, List[NegotiationMessage]] = {
            self.initiator: [],
            self.partner: []
        }

    def new_initiator_message(self, offer: float = 0) -> NegotiationMessage:
        msg = NegotiationMessage(self.initiator.name, self.partner.name, self.negotiation_item,
                                 self.conversation_id, self.round, offer)
        self.negotiation_history[self.initiator].append(msg)
        return msg

    def new_partner_message(self, offer: float = 0) -> NegotiationMessage:
        msg = NegotiationMessage(self.partner.name, self.initiator.name, self.negotiation_item,
                                 self.conversation_id, self.round, offer)
        self.negotiation_history[self.partner].append(msg)
        return msg

    def next_round(self) -> None:
        self.round += 1

    def agreement_reached(self) -> float:
        """
        Function that assesses the achievement of an agreement. It returns true if:
          - the partner responds with an offer that is LOWER_OR_EQUAL to what the the initiator proposed
            IN THE SAME ROUND
          - the initator makes an offer that is HIGHER_OR_EQUAL to what the responder proposed IN THE PREVIOUS ROUND

        Function returns 0 if negotiation not started, agreement conditions not met or number of rounds exceeded
        :return: The agreement that is advantageous for the initiator if agreement reached, 0 otherwise
        """
        if self.round == 0 and self.negotiation_history[self.initiator] and \
           self.negotiation_history[self.partner]:
            # if the first round of conversation has passed check if response to initiator proposal is a match
            initiator_proposal = self.negotiation_history[self.initiator][self.round]
            partner_response = self.negotiation_history[self.partner][self.round]

            print('initiator proposol offer : ',initiator_proposal.offer)
            print('partner proposol offer : ',partner_response.offer)
            
            if initiator_proposal.offer >= partner_response.offer:
                return partner_response.offer

        elif self.round > 0 and self.round < self.num_rounds:
            # if proposal in current round from initiator is HIGHER THAN response form partner in previous round
            # OR partner response in THIS round is LOWER than initiator proposal
            initiator_proposal = self.negotiation_history[self.initiator][self.round]
            partner_response_prev = self.negotiation_history[self.partner][self.round - 1]

            if initiator_proposal.offer >= partner_response_prev.offer:
                return initiator_proposal.offer
            else:
                if len(self.negotiation_history[self.partner]) > self.round:
                    partner_response = self.negotiation_history[self.partner][self.round]
                    if initiator_proposal.offer >= partner_response.offer:
                        return partner_response.offer

        return 0

    def protocol_respected_initiator(self) -> bool:
        """
        Function that checks if the monotonic concession protocol is respected between agents
        :return: True if protocol respected, False otherwise
        """
        if self.round > 0:
            proposal_prev = self.negotiation_history[self.initiator][self.round - 1]
            proposal = self.negotiation_history[self.initiator][self.round]

            if proposal.offer > proposal_prev.offer:
                return True
            else:
                self.failed = True
                return False

        return True

    def protocol_respected_partner(self) -> bool:
        """
        Function that checks if the monotonic concession protocol is respected between agents
        :return: True if protocol respected, False otherwise
        """
        if self.round > 0:
            proposal_prev = self.negotiation_history[self.partner][self.round - 1]
            proposal = self.negotiation_history[self.partner][self.round]

            if proposal.offer < proposal_prev.offer:
                return True
            else:
                self.failed = True
                return False

        return True

    def is_failed(self):
        return self.failed or self.round >= self.num_rounds
