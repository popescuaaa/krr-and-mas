from base import Environment
from typing import List, Dict, Any
import yaml

from agents import HouseOwnerAgent, CompanyAgent
from communication import MonotonicConcessionNegotiation

import logging.config

with open('logging_conf.yaml', 'r') as f:
    log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)
logger = logging.getLogger("environment")

"""
CONSTRUCTION PHASES
"""
STRUCTURAL_DESIGN = "structural design"
STRUCTURE_BUILDING = "structure building"
INTERIOR_DESIGN = "interior design"
ELECTRICS_PLUMBING = "electrics and plumbing"

"""
ENVIRONMENT IMPLEMENTATION
"""


class BuildingEnvironment(Environment):
    NR_AUCTION_ROUNDS = "nr_auction_rounds"
    NR_NEGOTIATION_ROUNDS = "nr_negotiation_rounds"
    AGENTS = "agents"
    AGENT_MODULE = "module"
    AGENT_CLASS = "class"
    AGENT_ROLES = "roles"
    BUDGET_ELEMENTS = "elements"
    COMPANIES = "companies"
    SPECIALTIES = "specialties"

    def __init__(self, owner_cfg_file: str, companies_cfg_file: str, game_cfg_file: str):
        super(BuildingEnvironment, self).__init__()

        self._owner_cfg_file: str = owner_cfg_file
        self._companies_cfg_file: str = companies_cfg_file
        self._game_cfg_file: str = game_cfg_file

        self._company_agents: List[CompanyAgent] = []
        self._owner_agent: HouseOwnerAgent = None

        self._num_auction_rounds = 3
        self._num_negotiation_rounds = 3

        self._construction_items = [STRUCTURAL_DESIGN, STRUCTURE_BUILDING, ELECTRICS_PLUMBING, INTERIOR_DESIGN]
        self._crt_item_idx: int = 0

        self._auction_stage = True
        self._auction_status = {
            STRUCTURAL_DESIGN: {"round": 0, "completed": False, "selected": []},
            STRUCTURE_BUILDING: {"round": 0, "completed": False, "selected": []},
            ELECTRICS_PLUMBING: {"round": 0, "completed": False, "selected": []},
            INTERIOR_DESIGN: {"round": 0, "completed": False, "selected": []},
        }

        self._negotiation_stage = False
        self._negotiation_status: Dict[str, Dict[str, Any]] = {
            STRUCTURAL_DESIGN: {"completed": False, "winner": None, "negotiations": []},
            STRUCTURE_BUILDING: {"completed": False, "winner": None, "negotiations": []},
            ELECTRICS_PLUMBING: {"completed": False, "winner": None, "negotiations": []},
            INTERIOR_DESIGN: {"completed": False, "winner": None, "negotiations": []},
        }

        self._finished = False
        self._game_status_str = None

        self._attributed_items: Dict[str, CompanyAgent] = {}

    @staticmethod
    def __get_company_config(companies: List[Dict[str, Any]], role: str):
        for comp in companies:
            if comp["name"] == role:
                return comp

        return None

    def add_company_agent(self, agent: CompanyAgent):
        self._company_agents.append(agent)

    def set_owner_agent(self, agent: HouseOwnerAgent):
        self._owner_agent = agent

    def initialize(self):
        """
        Initializes the house building environment with attributes provided in the yml config file with
        which the environment was instantiate
        """
        owner_cfg = None
        companies_cfg = None
        game_cfg = None

        with open(self._owner_cfg_file) as f:
            owner_cfg = yaml.load(f, Loader=yaml.FullLoader)

        with open(self._companies_cfg_file) as f:
            companies_cfg = yaml.load(f, Loader=yaml.FullLoader)

        with open(self._game_cfg_file) as f:
            game_cfg = yaml.load(f, Loader=yaml.FullLoader)

        self._num_auction_rounds = game_cfg[BuildingEnvironment.NR_AUCTION_ROUNDS]
        self._num_negotiation_rounds = game_cfg[BuildingEnvironment.NR_NEGOTIATION_ROUNDS]

        for ag_data in game_cfg[self.AGENTS]:
            agent_module = "agents." + ag_data[BuildingEnvironment.AGENT_MODULE]
            agent_class = ag_data[BuildingEnvironment.AGENT_CLASS]

            mod = __import__(agent_module, fromlist=[agent_class])
            klass = getattr(mod, agent_class)

            if "ACME" in ag_data[BuildingEnvironment.AGENT_ROLES]:
                agent = klass("ACME", owner_cfg[BuildingEnvironment.BUDGET_ELEMENTS])
                self.set_owner_agent(agent)
            else:
                for role in ag_data[BuildingEnvironment.AGENT_ROLES]:
                    comp_config = BuildingEnvironment.__get_company_config(
                        companies_cfg[BuildingEnvironment.COMPANIES],
                        role
                    )

                    if comp_config:
                        agent = klass(role, comp_config[BuildingEnvironment.SPECIALTIES])
                        self.add_company_agent(agent)

    def step(self):

        # Stage 1 - auction stage
        if self._auction_stage:

            auction_item = self._construction_items[self._crt_item_idx]
            print('[Auction stage]')
            print("Item  : ", auction_item, end='')
            if self._auction_status[auction_item]["completed"]:
                self._crt_item_idx += 1
            else:
                auction_round = self._auction_status[auction_item]["round"]
                if auction_round < self._num_auction_rounds:

                    # send an AuctioneerPerception to the house owner
                    item_budget = self._owner_agent.propose_item_budget(auction_item, auction_round)

                    print(' /', item_budget)

                    # send a BidderPerception to the company agents
                    agent_bids: Dict[CompanyAgent, float] = {}
                    for ag in self._company_agents:
                        if ag.has_specialty(auction_item):
                            bid = ag.decide_bid(auction_item, auction_round, item_budget)
                            agent_bids[ag] = bid

                    print("    agent _bids : ", agent_bids.values())

                    # send result of auction round to house owner
                    responding_agents = [ag.name for ag in agent_bids if agent_bids[ag]]
                    print("responding agent are : ", responding_agents)

                    self._owner_agent.notify_auction_round_result(auction_item, auction_round, responding_agents)

                    # inform responding agent that they have won the auction
                    for ag in [ag for ag in agent_bids if agent_bids[ag]]:
                        ag.notify_won_auction(auction_item, auction_round, len(responding_agents))

                    # if there were any respondents the auction for the current auction item ends and one can move on
                    if responding_agents:
                        self._auction_status[auction_item]["completed"] = True
                        self._auction_status[auction_item]["selected"] = [ag for ag in agent_bids if agent_bids[ag]]
                        self._crt_item_idx += 1
                        logger.info("[NOTIFICATION] Companies " + str(responding_agents) +
                                    " have accepted construction item " + auction_item + " at price: " +
                                    str(item_budget))

                        if self._crt_item_idx == len(self._construction_items):
                            # At this point the auction stage is finished
                            self._auction_stage = False
                            self._negotiation_stage = True
                            self._crt_item_idx = 0
                            logger.info("[NOTIFICATION] The Auction Phase has finished.")
                    else:
                        # increase round count
                        self._auction_status[auction_item]["round"] = auction_round + 1
                else:
                    # if number of auction round have passed, the game is lost by the home owner
                    self._finished = True
                    logger.info("[NOTIFICATION] GAME ENDED UNSUCCESSFULLY! House owner could not secure contract " +
                                "for item %s after %i rounds\n" % (auction_item, auction_round))

        elif self._negotiation_stage:
            print('[Negotiation stage]')
            # Stage 2 - negotiation stage

            if self._crt_item_idx < len(self._construction_items):
                negotiation_item = self._construction_items[self._crt_item_idx]  # select current negotiation item

                # if negotiation(s) for this construction has not started, create one/some
                if not self._negotiation_status[negotiation_item]["negotiations"]:
                    for partner_ag in self._auction_status[negotiation_item]["selected"]:
                        negotiation_conv = MonotonicConcessionNegotiation(self._owner_agent, partner_ag,
                                                                          negotiation_item,
                                                                          self._num_negotiation_rounds)
                        self._negotiation_status[negotiation_item]["negotiations"].append(negotiation_conv)

                        # get first offer from initiator
                        initial_offer = self._owner_agent.provide_negotiation_offer(negotiation_item, partner_ag.name,
                                                                                    negotiation_conv.round)
                        initial_offer_msg = negotiation_conv.new_initiator_message(offer=initial_offer)

                        # get initial response for partner agent
                        response_offer = partner_ag.respond_to_offer(initial_offer_msg)
                        response_offer_msg = negotiation_conv.new_partner_message(offer=response_offer)
                        self._owner_agent.notify_partner_response(response_offer_msg)

                # negotiation under way, see if agreement reached or protocol followed
                if self._negotiation_status[negotiation_item]["completed"]:
                    logger.info("[NOTIFICATION] Construction item %s assigned to %s!"
                                % (negotiation_item, self._negotiation_status[negotiation_item]["winner"]))
                    self._crt_item_idx += 1
                else:
                    # check if after after a proposal by initiator and response by partner agreement is reached
                    best_response_ag: CompanyAgent = None
                    best_response: float = 0

                    active_negotiations = [n for n in self._negotiation_status[negotiation_item]["negotiations"]
                                           if not n.is_failed()]
                    if not active_negotiations:
                        logger.info("[NOTIFICATION] GAME ENDED UNSUCCESSFULLY! Owner Agent failed to "
                                    "negotiate properly for construction item %s" % negotiation_item)
                        self._finished = True
                        return

                    for negotiation_conv in active_negotiations:
                        negotiation_result = negotiation_conv.agreement_reached()
                        if negotiation_result:
                            if best_response_ag is None:
                                best_response = negotiation_result
                                best_response_ag = negotiation_conv.partner
                            elif negotiation_result < best_response:
                                best_response = negotiation_result
                                best_response_ag = negotiation_conv.partner

                    if best_response_ag:
                        # if there is a winner, announce it and end negotiation for current construction item
                        self._negotiation_status[negotiation_item]["winner"] = best_response_ag
                        self._negotiation_status[negotiation_item]["completed"] = True
                        self._owner_agent.notify_negotiation_winner(negotiation_item, best_response_ag.name,
                                                                    best_response)
                        best_response_ag.notify_contract_assigned(negotiation_item, best_response)

                        for ag in self._auction_status[negotiation_item]["selected"]:
                            if ag != best_response_ag:
                                ag.notify_negotiation_lost(negotiation_item)

                    else:
                        # another negotiation round has to take place
                        active_negotiations = [n for n in self._negotiation_status[negotiation_item]["negotiations"]
                                               if not n.is_failed()]
                        if not active_negotiations:
                            logger.info("[NOTIFICATION] GAME ENDED UNSUCCESSFULLY! Owner Agent failed to "
                                        "negotiate properly for construction item %s" % negotiation_item)
                            self._finished = True
                            return

                        for negotiation_conv in active_negotiations:
                            # initiate next round
                            negotiation_conv.next_round()

                            # get owner offer
                            owner_offer = self._owner_agent.provide_negotiation_offer(negotiation_item,
                                                                                      negotiation_conv.partner.name,
                                                                                      negotiation_conv.round)
                            owner_offer_msg = negotiation_conv.new_initiator_message(offer=owner_offer)

                            if negotiation_conv.protocol_respected_initiator():
                                # test if new offer made by owner agent leads to protocol end
                                negotiation_result = negotiation_conv.agreement_reached()
                                if negotiation_result:
                                    if best_response_ag is None:
                                        best_response = negotiation_result
                                        best_response_ag = negotiation_conv.partner
                                    elif negotiation_result < best_response:
                                        best_response = negotiation_result
                                        best_response_ag = negotiation_conv.partner
                                else:
                                    # if owner offer does not close protocol, get a response from partner
                                    response_offer = negotiation_conv.partner.respond_to_offer(owner_offer_msg)
                                    response_offer_msg = negotiation_conv.new_partner_message(offer=response_offer)

                                    # if partner respects protocol, send partner response to owner agent
                                    if negotiation_conv.protocol_respected_partner():
                                        self._owner_agent.notify_partner_response(response_offer_msg)

                            if best_response_ag:
                                # if one of the negotiations finished succesfully end the negotiation for this item
                                self._negotiation_status[negotiation_item]["winner"] = best_response_ag
                                self._negotiation_status[negotiation_item]["completed"] = True
                                self._owner_agent.notify_negotiation_winner(negotiation_item, best_response_ag.name,
                                                                            best_response)
                                best_response_ag.notify_contract_assigned(negotiation_item, best_response)
                                for ag in self._auction_status[negotiation_item]["selected"]:
                                    if ag != best_response_ag:
                                        ag.notify_negotiation_lost(negotiation_item)
            else:
                self._negotiation_stage = False
                self._finished = True
                return
        else:
            self._finished = True
            return

    def goals_completed(self):
        return self._finished

    def __str__(self):
        res = "#### House Building Environment ####" + "\n"
        if self._game_status_str:
            res += self._game_status_str
        return res


if __name__ == "__main__":
    env = BuildingEnvironment(owner_cfg_file="config-ACME-project.cfg",
                              companies_cfg_file="config-companies-2.cfg",
                              game_cfg_file="game.cfg")
    env.initialize()

    while not env.goals_completed():
        env.step()
        print(env)
