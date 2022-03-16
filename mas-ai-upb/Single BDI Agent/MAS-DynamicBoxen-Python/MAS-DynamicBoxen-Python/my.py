from environment import *
import time


class MyAgent(BlocksWorldAgent):

    def __init__(self, name: str, desired_state: BlocksWorld):
        super(MyAgent, self).__init__(name=name)

        self.desired_state = desired_state
        self.desired_stacks = desired_state.stacks

        self.my_plan = []
        self.previous_action = None
        self.locked_stacks = []  # what I have accomplished

        # The current block which is in hand
        self.holding = None

        # The current state of the environment in terms of stacks (known)
        self.beliefs = {}  # block, associated stack

    def response(self, perception: BlocksWorldPerception):
        # TODO: revise beliefs; if necessary, make a plan; return an action.
        # raise NotImplementedError("not implemented yet; todo by student")

        return NoAction()

    def revise_beliefs(self, perceived_world_state: BlocksWorld):
        # TODO: check if what the agent knows corresponds to what the agent sees
        # raise NotImplementedError("not implemented yet; todo by student")

        blocks = perceived_world_state.get_all_blocks()
        if len(self.beliefs) == 0:
            for block in blocks:
                if block not in self.beliefs:
                    try:
                        associated_stack = perceived_world_state.get_stack(block)
                        self.beliefs[block] = associated_stack
                    except ValueError:
                        self.beliefs[block] = None

            return True  # has changed
        else:
            for block in blocks:
                known_stack = self.beliefs[block]
                real_world_stack = perceived_world_state.get_stack(block)

                if known_stack != real_world_stack:
                    return True

        return False

    def plan(self) -> List[BlocksWorldAction]:
        # TODO: return a new plan, as a sequence of `BlocksWorldAction' instances, based on the agent's knowledge.
        self.my_plan.append(NoAction())
        return self.my_plan

    def status_string(self):
        # TODO: return information about the agent's current state and current plan.
        return str(self) + " : PLAN MISSING"


class Tester(object):
    STEP_DELAY = 0.5
    TEST_SUITE = "tests/0e-large/"

    EXT = ".txt"
    SI = "si"
    SF = "sf"

    DYNAMICITY = 0.0

    AGENT_NAME = "*A"

    def __init__(self):
        self._environment = None
        self._agents = []

        self._initialize_environment(Tester.TEST_SUITE)
        self._initialize_agents(Tester.TEST_SUITE)

    def _initialize_environment(self, test_suite: str) -> None:
        filename = test_suite + Tester.SI + Tester.EXT

        with open(filename) as input_stream:
            self._environment = DynamicEnvironment(BlocksWorld(input_stream=input_stream))

    def _initialize_agents(self, test_suite: str) -> None:
        filename = test_suite + Tester.SF + Tester.EXT

        agent_states = {}

        with open(filename) as input_stream:
            desires = BlocksWorld(input_stream=input_stream)
            agent = MyAgent(Tester.AGENT_NAME, desires)

            agent_states[agent] = desires
            self._agents.append(agent)

            self._environment.add_agent(agent, desires, None)

            print("Agent %s desires:" % str(agent))
            print(str(desires))

    def make_steps(self):
        print("\n\n================================================= INITIAL STATE:")
        print(str(self._environment))
        print("\n\n=================================================")

        completed = False
        nr_steps = 0

        while not completed:
            completed = self._environment.step()

            time.sleep(Tester.STEP_DELAY)
            print(str(self._environment))

            for ag in self._agents:
                print(ag.status_string())

            nr_steps += 1

            print("\n\n================================================= STEP %i completed." % nr_steps)

        print("\n\n================================================= ALL STEPS COMPLETED")


if __name__ == "__main__":
    tester = Tester()
    tester.make_steps()
