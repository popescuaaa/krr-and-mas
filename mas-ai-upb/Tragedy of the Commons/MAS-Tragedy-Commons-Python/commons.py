from base import Agent, Environment
from communication import AgentAction
from typing import List, Dict, Callable
import yaml
import random
import math

class CommonsPerception(object):
    """
    The perception data structure received by agents in the Tragedy of the Commons scenario
    """
    def __init__(self, destination_id: int, resource_quantity: float, resource_remaining: float, num_agents: int,
                 resource_shares: Dict[int, float] = None,
                 aggregate_adjustment: Dict[int, float] = None,
                 round_finished: bool = False,
                 agent_utilities: Dict[int, float] = None):
        """
        :param destination_id:
        :param resource_quantity:
        :param resource_remaining:
        :param resource_shares:
        :param aggregate_adjustment:
        :param round_finished:
        :param agent_utilities
        """
        self.destination_id = destination_id

        self.resource_quantity = resource_quantity
        self.resource_remaining = resource_remaining

        self.num_agents = num_agents

        self.resource_shares = resource_shares
        self.aggregate_adjustment = aggregate_adjustment
        self.round_finished = round_finished
        
        self.agent_utilities = agent_utilities


class CommonsAgent(Agent):
    """
    Parent class for agents in the tragedy of the commons scenario.
    """
    def __init__(self, agent_id: int):
        """
        Default constructor for CommonsAgent
        """
        self.id = agent_id
        self.name = self.__class__.__name__ + "_" + str(agent_id)
        self.utility_score = 0

    def specify_share(self, perception: CommonsPerception) -> float:
        raise NotImplementedError("Must be implemented by student")

    def negotiation_response(self, negotiation_round: int, perception: CommonsPerception,
                             utility_func: Callable[[float, float, List[float]], float]) -> AgentAction:
        raise NotImplementedError("Must be implemented by student")

    def inform_round_finished(self, negotiation_round: int, perception: CommonsPerception):
        pass

    def __eq__(self, other):
        """
        Two agents are equal if their ID's are the same
        :param other: the other agent
        :return: True if the `other' agent has the same ID as this one
        """
        if isinstance(other, self.__class__):
            return self.id == other.id
        else:
            return False

    def __hash__(self):
        return self.id

    def __str__(self):
        return "%s" % self.name


class CommonsEnvironment(Environment):
    RESOURCE_QUANTITY   = "nr_resources"
    NR_ROUNDS           = "nr_rounds"
    NR_ADJUST_ROUNDS    = "nr_adjust_rounds"
    CHANCE_REPLENISH    = "chance_replenish"
    CHANCE_DEVIATION    = "chance_deviation"
    FRACTION_DEVIATION  = "fraction_deviation"
    AGENTS              = "agents"
    START_ID            = "start_id"
    END_ID              = "end_id"
    AGENT_MODULE        = "module"
    AGENT_CLASS         = "class"


    def __init__(self, config_file):
        super(CommonsEnvironment, self).__init__()

        self._config_file: str = config_file

        self.resource_quantity: float = 0
        self._chance_replenish: float = .0
        self._chance_deviation: float = .0
        self._fraction_deviation: float = .0
        self.commons_agents: List[CommonsAgent] = []

        self._crt_round: int = 0
        self._total_rounds: int = 0
        self._adjust_rounds: int = 4
        self._finished = False

        self._utility_scores: List[float] = []
        self._individual_utility_scores: List[Dict[CommonsAgent, float]] = []
        self._individual_shares: List[Dict[CommonsAgent, float]] = []


    def add_agent(self, agent: CommonsAgent):
        self.commons_agents.append(agent)


    def initialize(self, rand_seed = None):
        """
        Initializes the commons environment with attributes provided in the yml config file with
        which the environment was instantiated
        :param rand_seed: Seed for random number generator. May be None
        """
        with open(self._config_file) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)

            self.resource_quantity = data[CommonsEnvironment.RESOURCE_QUANTITY]
            self._total_rounds = data[CommonsEnvironment.NR_ROUNDS]
            self._adjust_rounds = data[CommonsEnvironment.NR_ADJUST_ROUNDS]
            self._chance_replenish = data[CommonsEnvironment.CHANCE_REPLENISH]
            self._chance_deviation = data[CommonsEnvironment.CHANCE_DEVIATION]
            self._fraction_deviation = data[CommonsEnvironment.FRACTION_DEVIATION]

            for ag_data in data[CommonsEnvironment.AGENTS]:
                if ag_data[CommonsEnvironment.START_ID] == ag_data[CommonsEnvironment.END_ID]:
                    agent_id = ag_data[CommonsEnvironment.START_ID]
                    agent_module = "agents." + ag_data[CommonsEnvironment.AGENT_MODULE]
                    agent_class = ag_data[CommonsEnvironment.AGENT_CLASS]

                    mod = __import__(agent_module, fromlist=[agent_class])
                    klass = getattr(mod, agent_class)

                    agent = klass(agent_id)
                    self.add_agent(agent)
                else:
                    for agent_id in range(ag_data[CommonsEnvironment.START_ID], ag_data[CommonsEnvironment.END_ID] + 1):
                        agent_module = "agents." + ag_data[CommonsEnvironment.AGENT_MODULE]
                        agent_class = ag_data[CommonsEnvironment.AGENT_CLASS]

                        mod = __import__(agent_module, fromlist=[agent_class])
                        klass = getattr(mod, agent_class)

                        agent = klass(agent_id)
                        self.add_agent(agent)



    def __commons_utility(self, K: float, resource_shares: List[float]) -> float:
        """
        Computes the society wide utility, given an amount of resource K and the shares wanted by each agent
        :param K:
        :param resource_shares:
        :return:
        """
        share_total = sum(resource_shares)
        if share_total >= 1:
            return 0

        score = sum([math.log(K * share) for share in resource_shares if K*share >= 1])
        score += len(resource_shares) * math.log(K - K*share_total) if K - K*share_total >= 1 else 0

        return score

    def __agent_utility(self, K: float, agent_share: float, all_shares: List[float]) -> float:
        """
        Computes the individual utility of an agent given his agent_share and all_shares of the agent society
        :param K:
        :param agent_share:
        :param all_shares:
        :return:
        """
        share_total = sum(all_shares)
        if share_total >= 1:
            return 0

        personal_resource_consumption = K * agent_share
        remaining_resource = K - K * share_total

        personal_utility = math.log(personal_resource_consumption) if personal_resource_consumption >= 1 else 0
        remaining_utility = math.log(remaining_resource) if remaining_resource >= 1 else 0

        return personal_utility + remaining_utility


    def __deviated_utility(self, deviation: float = None):
        """
        Computes an allowed deviation at each turn, whereby agent utilities for the same resource amount and list of
        societal shares may differ by a given amount
        :param deviation: deviation percentage
        :return:
        """
        def utility(K: float, agent_share, all_shares: List[float]) -> float:
            agent_utility = self.__agent_utility(K, agent_share, all_shares=all_shares)
            if deviation:
                utility_deviation = deviation * math.log(K / (len(all_shares) + 1))
                agent_utility += utility_deviation

            return agent_utility

        return utility
    
    def __adjust_shares(self, agent_shares: Dict[int, float] = None, adjustments: Dict[int, float] = None):
        if adjustments:
            for agent_id in agent_shares:
                agent_shares[agent_id] += adjustments.get(agent_id, 0)
            
        return agent_shares


    def __get_utility_functions(self) -> Dict[Agent, Callable[[float, float, List[float]], float]]:
        """
        Creates a mapping of the agent utility functions at each environment turn
        :return:
        """
        num_agents = len(self.commons_agents)
        utility_dict = dict([(agent, self.__deviated_utility()) for agent in self.commons_agents])

        if random.random() < self._chance_deviation:
            agent_indexes = range(num_agents)
            num_changes = num_agents // 8

            if num_changes >= 1:
                positive_change_indexes = random.sample(agent_indexes, num_changes)
                agent_indexes = [idx for idx in agent_indexes if not idx in positive_change_indexes]
                negative_change_indexes = random.sample(agent_indexes, num_changes)

                for idx in positive_change_indexes:
                    utility_dict[self.commons_agents[idx]] = self.__deviated_utility(deviation=self._fraction_deviation)

                for idx in negative_change_indexes:
                    utility_dict[self.commons_agents[idx]] = self.__deviated_utility(deviation=-self._fraction_deviation)

        return utility_dict


    def step(self):
        if self.resource_quantity:
            ## if there was any resource left from the previous step, it may get replenished
            chance = random.random()
            if chance < self._chance_replenish:
                self.resource_quantity *= 2

            num_agents = len(self.commons_agents)

            # Stage 0: compute deviations if there are any
            agent_utility_funcs = self.__get_utility_functions()

            # Stage 1: deliver perceptions of available resource in this round
            agent_shares: Dict[int, float] = {}
            for agent in self.commons_agents:
                ag_perception = CommonsPerception(agent.id, self.resource_quantity, self.resource_quantity, num_agents)
                agent_shares[agent.id] = agent.specify_share(ag_perception)

            ag_utilites = {ag.id: agent_utility_funcs[ag](self.resource_quantity, agent_shares[ag.id],
                                                             list(agent_shares.values())) for ag in self.commons_agents}

            # Stage 2: enter negotiation rounds while there is at least one agent that has an adjust action
            agg_adjustment = None
            adjust_round = 0
            while adjust_round < self._adjust_rounds:
                remaining_resource = max(.0, self.resource_quantity * (1.0 - sum(agent_shares.values())))
                round_finished = False

                agent_actions: Dict[Agent, AgentAction] = {}
                for agent in self.commons_agents:
                    ag_perception = CommonsPerception(agent.id, self.resource_quantity, remaining_resource, num_agents,
                                                      aggregate_adjustment=agg_adjustment,
                                                      resource_shares=agent_shares,
                                                      agent_utilities=ag_utilites)
                    act = agent.negotiation_response(adjust_round, ag_perception,
                                                     utility_func=agent_utility_funcs[agent])
                    if act.consumption_adjustment and abs(sum(act.consumption_adjustment.values())) > 1e-9:
                        print("[Illegal adjustment] Agent %s has proposed an adjustment for other"
                              " agents that does not have a 0 balance" % agent.name)
                        round_finished = True
                        break
                    agent_actions[agent] = agent.negotiation_response(adjust_round, ag_perception,
                                                                      utility_func=agent_utility_funcs[agent])

                if round_finished:
                    break
                else:
                    round_finished = all([act.no_action for act in agent_actions.values()])
                    if round_finished:
                        # finish the adjustment rounds
                        break
                    else:
                        # it means at least some agent proposes an adjustment
                        # aggregate the results by averaging adjustment proposals
                        agent_shares = dict([(agent.id, act.resource_share) for (agent, act) in agent_actions.items()])
                        
                        nr_submitted_adjustments = sum([1 for act in agent_actions.values() if not act.no_action])
                        agg_adjustment = {}
                        for agent in self.commons_agents:
                            adjustment_list = list(filter(lambda x: x != 0, [act.consumption_adjustment[agent.id]
                                                    for act in agent_actions.values()]))
                            if adjustment_list:
                                agg_adjustment[agent.id] = sum(adjustment_list) / nr_submitted_adjustments
                            else:
                                agg_adjustment[agent.id] = 0

                adjust_round += 1
            
            # if all adjustment rounds have finished, adjust shares as result of negotiations,
            # compute remaining resource and real societal utility score
            agent_shares = self.__adjust_shares(agent_shares=agent_shares, adjustments=agg_adjustment)
            remaining_resource = max(.0, self.resource_quantity * (1.0 - sum(agent_shares.values())))
            
            # then inform the agents of the round end
            ag_utilites = {ag.id: agent_utility_funcs[ag](self.resource_quantity, agent_shares[ag.id],
                                                          list(agent_shares.values())) for ag in self.commons_agents}
            
            utility_score = 0
            agent_utilites = {}
            logged_shares = {}
            for agent in self.commons_agents:
                agent.inform_round_finished(adjust_round, CommonsPerception(agent.id, self.resource_quantity,
                                                            remaining_resource, num_agents,
                                                            aggregate_adjustment=agg_adjustment,
                                                            resource_shares=agent_shares,
                                                            round_finished=True,
                                                            agent_utilities=ag_utilites))
                agent_utilites[agent] = agent_utility_funcs[agent](self.resource_quantity, agent_shares[agent.id],
                                                             list(agent_shares.values()))
                utility_score += agent_utilites[agent]
                logged_shares[agent] = agent_shares[agent.id]

            self._individual_utility_scores.append(agent_utilites)
            self._individual_shares.append(logged_shares)
            self._utility_scores.append(utility_score)

            # update resource quantity and increment round counter
            self.resource_quantity = remaining_resource
            self._crt_round += 1
        else:
            self._finished = True
            return


    def goals_completed(self):
        return self._finished or self._crt_round >= self._total_rounds


    def __str__(self):
        res = "#### Commons Environment ####" + "\n"

        if self._crt_round > 0:
            res += "\t" + " - " + "Round %i out of %i" % (self._crt_round, self._total_rounds) + "\n"
            res += "\t" + " - " + "Remaining resource quantity: %f" % self.resource_quantity + "\n"

            p = sum(self._individual_shares[self._crt_round - 1].values())
            res += "\t" + " - " + "Consumed resource quantity: %f" \
                   % (p * self.resource_quantity / (1 - p)) + "\n"
            res += "\t" + " - " + "Real Collective Utility: %f" % self._utility_scores[self._crt_round - 1] + "\n"

            res += "\t" + " - " + "Individual Shares: " + "\n"
            for agent, share in self._individual_shares[self._crt_round - 1].items():
                res += "\t\t" + " - " + "(%s: %f)" % (agent.name, share) + "\n"

            res += "\t" + " - " + "Individual Utility: " + "\n"
            for agent, utility in self._individual_utility_scores[self._crt_round - 1].items():
                res += "\t\t" + " - " + "(%s: %f)" % (agent.name, utility) + "\n"

        else:
            res += "\t" + " - " + "Initial resource quantity: %f" % self.resource_quantity + "\n"


        return res


if __name__ == "__main__":
    env = CommonsEnvironment(config_file="config.cfg")
    env.initialize()
    print(env)

    while not env.goals_completed():
        env.step()
        print(env)

