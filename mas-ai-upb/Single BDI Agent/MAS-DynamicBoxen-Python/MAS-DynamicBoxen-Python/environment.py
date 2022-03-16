from blocksworld import *
from base import Environment, Agent, Perception
import random

""" ======================================== Blocksworld agent ======================================== """


class BlocksWorldPerception(Perception):
    def __init__(self, current_world: BlocksWorld, current_station: Station, previous_action_succeeded: bool):
        super(BlocksWorldPerception, self).__init__()

        self.current_world = current_world
        self.current_station = current_station
        self.previous_action_succeeded = previous_action_succeeded


class BlocksWorldAgent(Agent):
    """
    Base class to be implemented by agent implementations. A reactive agent is only defined by its Agent @ to
    perceptions.
    """

    def __init__(self, name=None):
        super(BlocksWorldAgent, self).__init__(name)

    def response(self, perception: BlocksWorldPerception) -> BlocksWorldAction:
        """
        Supplies the agent with perceptions and demands one action from the agent. The environment also specifies if the
        previous action of the agent has succeeded or not.

        :param perception: the perceptions offered by the environment to the agent.
        :return: he agent output, containing the action to perform. Action should be of type
        {@link blocksworld.BlocksWorldAction.Type#NONE} if the agent is not performing an action now,
        but may perform more actions in the future.
        Action should be of type {@link blocksworld.BlocksWorldAction.Type#AGENT_COMPLETED} if the agent will not
        perform any more actions ever in the future.
        """
        raise NotImplementedError("Missing a response")

    def status_string(self):
        """
        :return: a string that is printed at every cycle to show the status of the agent.
        """
        return NotImplementedError("Missing a status string")

    def __str__(self):
        """
        :return: The agent name
        """
        return "A"


class AgentData(object):
    """
    Contains data for each agent in the environment
    """

    def __init__(self, linked_agent: BlocksWorldAgent, target: BlocksWorld, initial_station: Station):
        """
        Default constructor.
        :param linked_agent: the agent
        :param target: the desired state of the agent
        :param initial_station: the initial position of the agent (the station at which it is located)
        """
        self.agent = linked_agent
        self.target_state = target
        self.station = initial_station

        self.previous_action_succeeded = True
        self.holding = None

    def __str__(self):
        return "Agent %s at %s holding %s; previous action: %s" \
               % (str(self.agent),
                  str(self.station),
                  str(self.holding) if self.holding else "none",
                  "successful" if self.previous_action_succeeded else "failed")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.agent == other.agent
        else:
            return False


class BlocksWorldEnvironment(Environment):

    def __init__(self, world: BlocksWorld):
        self.worldstate = world.clone()
        self.agents_data = []

        idx = ord("0")
        self.station = Station(str(chr(idx)))

    def add_agent(self, agent: BlocksWorldAgent, desires, placement):
        self.agents_data.append(AgentData(linked_agent=agent, target=desires, initial_station=self.station))

    def _get_agent_data(self, agent: Agent):
        for adata in self.agents_data:
            if adata.agent == agent:
                return adata

        raise ValueError("Agent %s has not been added to the environment" % str(agent))

    def step(self) -> bool:
        print("\n".join([str(adata) for adata in self.agents_data]))

        completed = False

        for adata in self.agents_data:
            agent_station = adata.station
            world_stacks = self.worldstate.get_stacks()
            current_world = self.worldstate.clone()

            act = adata.agent.response(BlocksWorldPerception(current_world, agent_station,
                                                             adata.previous_action_succeeded))
            print("Agent %s opts for %s" % (str(adata.agent), str(act)))

            # set previous action succeeded as False, initially
            adata.previous_action_succeeded = False

            if (act.get_type() == "putdown" or act.get_type() == "stack") and \
                    (not adata.holding or adata.holding != act.get_first_arg()):
                raise RuntimeError("Can't work with that block [%s]; agent is holding [%s]"
                                   % (str(act.get_first_arg()), str(adata.holding)))

            if (act.get_type() == "pickup" or act.get_type() == "unstack") and adata.holding:
                raise RuntimeError("Can't work with that block [%s]; agent is holding [%s]"
                                   % (str(act.get_first_arg()), str(adata.holding)))

            if act.get_type() == "pickup":
                # modify world; remove station; switch agent to other station.
                block_in_stacks = False
                for stack in world_stacks:
                    if act.get_argument() in stack:
                        block_in_stacks = True
                        break

                if not block_in_stacks:
                    raise RuntimeError("The block [%s] is not present in any of the stacks " % str(act.get_argument()))

                adata.holding = self.worldstate.pick_up(act.get_argument())
                adata.station = self.station
                adata.previous_action_succeeded = True

            elif act.get_type() == "putdown":
                # modify world;
                # current stack is always the last one
                current_stack = world_stacks[-1]
                self.worldstate.put_down(act.get_argument(), current_stack)

                adata.holding = None
                adata.previous_action_succeeded = True

            elif act.get_type() == "unstack":
                block_in_stacks = False
                for stack in world_stacks:
                    if act.get_first_arg() in stack:
                        block_in_stacks = True
                        break

                if not block_in_stacks:
                    raise RuntimeError("The block [%s] is not in any of the current world stacks "
                                       % (str(act.get_first_arg())))

                adata.holding = self.worldstate.unstack(act.get_first_arg(), act.get_second_arg())
                adata.previous_action_succeeded = True

            elif act.get_type() == "stack":
                block_in_stacks = False
                for stack in world_stacks:
                    if act.get_second_arg() in stack:
                        block_in_stacks = True
                        break

                if not block_in_stacks:
                    raise RuntimeError("The block [%s] is not in any of the current world stacks"
                                       % (str(act.get_second_arg())))

                self.worldstate.stack(act.get_first_arg(), act.get_second_arg())
                adata.holding = None
                adata.previous_action_succeeded = True


            elif act.get_type() == "lock":
                block_in_stacks = False
                for stack in world_stacks:
                    if act.get_argument() in stack:
                        block_in_stacks = True
                        break

                if not block_in_stacks:
                    raise RuntimeError("The block [%s] is not in any of the current world stacks"
                                       % (str(act.get_argument())))

                self.worldstate.lock(act.get_argument())
                adata.previous_action_succeeded = True


            elif act.get_type() == "agent_completed":
                completed += 1
                adata.previous_action_succeeded = True

            elif act.get_type() == "no_action":
                adata.previous_action_succeeded = True

            else:
                raise RuntimeError("Should not be here: action not recognized %s" % act.get_type())

        if completed == len(self.agents_data):
            return True
        return False  # return True when the simulation should stop (only when all agents completed their goals)

    def __str__(self):
        prefix = {}

        for adata in self.agents_data:
            data = []
            data.append(" " + str(adata.agent))
            data.append(" <" + ("" if not adata.holding else str(adata.holding)) + ">")
            data.append("\n")
            prefix[self.worldstate.get_stacks()[0]] = data

        suffix = {}

        data = ["====="]
        data.append(" " + str(self.station))
        suffix[self.worldstate.get_stacks()[0]] = data

        return self.worldstate._print_world(6, prefixes=prefix, suffixes=suffix, print_table=False)


""" ========================================= DYNAMIC ENVIRONMENT ========================================= """


class DynamicAction(object):
    STASH = "stash"
    STASH_PROB = 0.15

    UNSTASH = "unstash"
    UNSTASH_PROB = 0.25

    DROP = "drop"
    DROP_PROB = 0.3

    TELEPORT = "teleport"
    TELEPORT_PROB = 0.3

    ACTIONS = [
        (STASH, STASH_PROB),
        (UNSTASH, UNSTASH_PROB),
        (DROP, DROP_PROB),
        (TELEPORT, TELEPORT_PROB)
    ]

    def __init__(self, type, probability):
        self.type = type
        self.probability = probability

    @staticmethod
    def pick():
        import random

        r = random.random()
        count_prob = 0
        for act in DynamicAction.ACTIONS:
            count_prob += act[1]
            if count_prob >= r:
                return DynamicAction(act[0], act[1])

        raise RuntimeError("Should not get here; probabilities are broken!")

    def __str__(self):
        return self.type


class DynamicEnvironment(BlocksWorldEnvironment):
    HEAD = "\t\t\t\t\t\t\t\t<DYNAMICS>"

    def __init__(self, world: BlocksWorld):
        super(DynamicEnvironment, self).__init__(world)
        self.stash = set([])

    def _perform_dynamic_action(self) -> None:
        from my import Tester

        if random.random() < Tester.DYNAMICITY:
            dyna = DynamicAction.pick()

            # print("[DYNAMIC ENV] selected action: " + str(dyna))

            observed_stacks = set(self.worldstate.get_stacks())

            if dyna.type == DynamicAction.STASH:
                s = self._pick_stack(True, False, observed_stacks)
                if not s:
                    return

                b = s.get_top_block()
                if s.is_single_block():
                    self.worldstate.pick_up(b)
                else:
                    self.worldstate.unstack(b, s.get_below(b))

                self.stash.add(b)
                print(DynamicEnvironment.HEAD + "[ %s ] -> stash" % str(b))

            elif dyna.type == DynamicAction.UNSTASH:
                if not self.stash:
                    return

                b = random.choice(list(self.stash))
                self.stash.remove(b)

                s = self._pick_stack(True, True, observed_stacks)
                self.worldstate.stack(b, s.get_top_block())
                print(DynamicEnvironment.HEAD + "[ %s ] : stash -> %s." % (str(b), str(s)))

            elif dyna.type == DynamicAction.DROP:
                s = self._pick_stack(False, False, observed_stacks)
                if not s:
                    return

                b = s.get_top_block()
                self.worldstate.unstack(b, s.get_below(b))
                self.worldstate.put_down(b, s)

                print(DynamicEnvironment.HEAD + " [ %s ] -> ___." % str(b))

            elif dyna.type == DynamicAction.TELEPORT:
                s = self._pick_stack(True, False, observed_stacks)
                if not s:
                    return

                b = s.get_top_block()
                if s.is_single_block():
                    self.worldstate.pick_up(b)
                else:
                    self.worldstate.unstack(b, s.get_below(b))

                s1 = self._pick_stack(True, True, observed_stacks)
                self.worldstate.stack(b, s1.get_top_block())

                print(DynamicEnvironment.HEAD + " [ %s ] : %s -> %s." % (str(b), str(s), str(s1)))

            else:
                raise RuntimeError("Unrecognized dynamic action type: %s" % dyna.type)

    def _pick_stack(self, can_be_single: bool, can_be_locked: bool, observed_stacks: Set[BlockStack]) -> BlockStack:
        choice_stacks = []
        for s in self.worldstate.get_stacks():
            if (can_be_single or not s.is_single_block()) and \
                    (can_be_locked or not s.is_locked(s.get_top_block())):
                choice_stacks.append(s)

        return None if not choice_stacks else random.choice(choice_stacks)

    def step(self):
        self._perform_dynamic_action()
        return super(DynamicEnvironment, self).step()

    def __str__(self):
        return super(DynamicEnvironment, self).__str__() + "Stash: %s \n" % (" ".join([str(b) for b in self.stash]))
