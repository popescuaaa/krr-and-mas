import random
import time
from enum import Enum
from pprint import pprint

from base import Action, Perception
from hunting import HuntingEnvironment, WildLifeAgentData, WildLifeAgent
from representation import GridRelativeOrientation, GridOrientation
from communication import AgentMessage, SocialAction

ID = 1


# Id helper
def generate_predator_id():
    global ID
    old_id = ID
    new_id = ID + 1
    ID = new_id
    return old_id


class ProbabilityMap(object):

    def __init__(self, existing_map=None):
        self.__internal_dict = {}

        if existing_map:
            for k, v in existing_map.list_actions():
                self.__internal_dict[k] = v

    def empty(self):
        if self.__internal_dict:
            return False

        return True

    def put(self, action, value):
        self.__internal_dict[action] = value

    def remove(self, action):
        """
        Updates a discrete action probability map by uniformly redistributing the probability of an action to remove over
        the remaining possible actions in the map.
        :param action: The action to remove from the map
        :return:
        """
        if action in self.__internal_dict:
            val = self.__internal_dict[action]
            del self.__internal_dict[action]

            remaining_actions = list(self.__internal_dict.keys())
            nr_remaining_actions = len(remaining_actions)

            if nr_remaining_actions != 0:
                prob_sum = 0
                for i in range(nr_remaining_actions - 1):
                    new_action_prob = (self.__internal_dict[remaining_actions[i]] + val) / float(nr_remaining_actions)
                    prob_sum += new_action_prob

                    self.__internal_dict[remaining_actions[i]] = new_action_prob

                self.__internal_dict[remaining_actions[nr_remaining_actions - 1]] = 1 - prob_sum

    def choice(self):
        """
        Return a random action from a discrete distribution over a set of possible actions.
        :return: an action chosen from the set of choices
        """
        r = random.random()
        count_prob = 0

        for a in self.__internal_dict.keys():
            count_prob += self.__internal_dict[a]
            if count_prob >= r:
                return a

        raise RuntimeError("Should never get to this point when selecting an action")

    def list_actions(self):
        return self.__internal_dict.items()


class MyAction(Action, Enum):
    """
    Physical actions for wildlife agents.
    """

    # The agent must move north (up)
    NORTH = 0

    # The agent must move east (right).
    EAST = 1

    # The agent must move south (down).
    SOUTH = 2

    # The agent must move west (left).
    WEST = 3


class MyAgentPerception(Perception):
    """
    The perceptions of a wildlife agent.
    """

    def __init__(self, agent_position, obstacles, nearby_predators, nearby_prey, messages=None):
        """
        Default constructor
        :param agent_position: agents's position.
        :param obstacles: visible obstacles
        :param nearby_predators: visible predators - given as tuple (agent_id, grid position)
        :param nearby_prey: visible prey - given as tuple (agent_id, grid_position)
        :param messages: incoming messages, may be None
        """
        self.agent_position = agent_position
        self.obstacles = obstacles
        self.nearby_predators = nearby_predators
        self.nearby_prey = nearby_prey

        if messages:
            self.messages = messages
        else:
            self.messages = []


class MyPrey(WildLifeAgent):
    """
    Implementation of the prey agent.
    """
    UP_PROB = 0.25
    LEFT_PROB = 0.25
    RIGHT_PROB = 0.25
    DOWN_PROB = 0.25

    def __init__(self):
        super(MyPrey, self).__init__(WildLifeAgentData.PREY)

    def response(self, perceptions):
        """
        TODO: your code here
        :param perceptions: The perceptions of the agent at each step
        :return: The `Action' that your agent takes after perceiving the environment at each step
        """
        agent_pos = perceptions.agent_position
        probability_map = ProbabilityMap()
        probability_map.put(MyAction.NORTH, MyPrey.UP_PROB)
        probability_map.put(MyAction.SOUTH, MyPrey.DOWN_PROB)
        probability_map.put(MyAction.WEST, MyPrey.LEFT_PROB)
        probability_map.put(MyAction.EAST, MyPrey.RIGHT_PROB)

        for obstacle_pos in perceptions.obstacles:
            if agent_pos.get_distance_to(obstacle_pos) > 1:
                continue

            relative_orientation = agent_pos.get_simple_relative_orientation(obstacle_pos)
            if relative_orientation == GridRelativeOrientation.FRONT:
                probability_map.remove(MyAction.NORTH)

            elif relative_orientation == GridRelativeOrientation.BACK:
                probability_map.remove(MyAction.SOUTH)

            elif relative_orientation == GridRelativeOrientation.RIGHT:
                probability_map.remove(MyAction.EAST)

            elif relative_orientation == GridRelativeOrientation.LEFT:
                probability_map.remove(MyAction.WEST)

        ## save available moves
        available_moves = ProbabilityMap(existing_map=probability_map)

        ## examine actions which are unavailable because of predators
        for (_, predator_pos) in perceptions.nearby_predators:
            relative_pos = agent_pos.get_simple_relative_orientation(predator_pos)

            if relative_pos == GridRelativeOrientation.FRONT:
                probability_map.remove(MyAction.NORTH)

            elif relative_pos == GridRelativeOrientation.FRONT_LEFT:
                probability_map.remove(MyAction.NORTH)
                probability_map.remove(MyAction.WEST)

            elif relative_pos == GridRelativeOrientation.FRONT_RIGHT:
                probability_map.remove(MyAction.NORTH)
                probability_map.remove(MyAction.EAST)

            elif relative_pos == GridRelativeOrientation.LEFT:
                probability_map.remove(MyAction.WEST)

            elif relative_pos == GridRelativeOrientation.RIGHT:
                probability_map.remove(MyAction.EAST)

            elif relative_pos == GridRelativeOrientation.BACK:
                probability_map.remove(MyAction.SOUTH)

            elif relative_pos == GridRelativeOrientation.BACK_LEFT:
                probability_map.remove(MyAction.SOUTH)
                probability_map.remove(MyAction.WEST)

            elif relative_pos == GridRelativeOrientation.BACK_RIGHT:
                probability_map.remove(MyAction.SOUTH)
                probability_map.remove(MyAction.EAST)

        if not probability_map.empty():
            return probability_map.choice()
        else:
            return available_moves.choice()


class MyPredator(WildLifeAgent):

    def __init__(self, map_width=None, map_height=None):
        super(MyPredator, self).__init__(WildLifeAgentData.PREDATOR)
        self.map_width = map_width
        self.map_height = map_height
        self.predators_memory = {}

    def response(self, perceptions):
        """
        TODO your response function for the predator agent
        :param perceptions:
        :return:
        """
        # Create a new instance for prop map in order to know which action to do

        print(perceptions.__dict__)
        current_position = perceptions.agent_position
        nearby_predators = perceptions.nearby_predators
        nearby_pray = perceptions.nearby_prey
        obstacles = perceptions.obstacles
        messages = perceptions.messages

        my_id = self.id

        current_predator_prob_map = ProbabilityMap(existing_map=None)

        # Remember predator friends (possible positions)
        for predator_id, predator_pos in nearby_predators:
            if predator_pos == current_position:
                my_id = predator_id

            if predator_id not in self.predators_memory and predator_pos != current_position:
                self.predators_memory[predator_id] = predator_pos

        # Find best pray
        best_pray = None
        for pray in nearby_pray:
            if best_pray is None:
                best_pray = pray
            else:
                if current_position.get_distance(pray) < current_position.get_distance(best_pray):
                    best_pray = pray

            # Check is a friend nearby
            for friend_id in self.predators_memory:
                messages.append(AgentMessage(sender_id=my_id, destination_id=friend_id, content=(current_position, pray)))

        # Create a prob map for predator actions
        if my_id % 4 == 0:
            # I am sent to kill, or I am the sweeper

            if current_position.get_neighbour_position(GridOrientation.SOUTH) in obstacles or \
                    current_position.get_neighbour_position(GridOrientation.WEST) in obstacles:

                if current_position.get_neighbour_position(GridOrientation.SOUTH) not in obstacles:
                    current_predator_prob_map.put(MyAction.SOUTH, 1)
                else:
                    current_predator_prob_map.put(MyAction.EAST, 1)
            else:
                if current_position.get_neighbour_position(GridOrientation.NORTH) in obstacles:
                    current_predator_prob_map.put(MyAction.WEST, 0.6)
                    current_predator_prob_map.put(MyAction.SOUTH, 0.4)
                else:
                    current_predator_prob_map.put(MyAction.NORTH, 0.8)
                    current_predator_prob_map.put(MyAction.WEST, 0.2)

        elif my_id % 2 == 0:
            current_predator_prob_map.put(MyAction.EAST, 0.22)
            current_predator_prob_map.put(MyAction.WEST, 0.28)
            current_predator_prob_map.put(MyAction.NORTH, 0.25)
            current_predator_prob_map.put(MyAction.SOUTH, 0.25)
        else:
            current_predator_prob_map.put(MyAction.EAST, 0.28)
            current_predator_prob_map.put(MyAction.WEST, 0.22)
            current_predator_prob_map.put(MyAction.NORTH, 0.25)
            current_predator_prob_map.put(MyAction.SOUTH, 0.25)

        if best_pray is None:
            # I check messages from my fellows
            for message in messages:
                content = message.content
                friend_id, friend_pray = content

                if best_pray is None:
                    best_pray = friend_pray
                else:
                    if current_position.get_distance(friend_pray) < current_position.get_distance(best_pray):
                        best_pray = friend_pray

        if best_pray is not None:
            # Take an action
            current_predator_prob_map.empty()
            _, pos = best_pray

            px, py = pos.x, pos.y
            mx, my = current_position.x, current_position.y

            if px < mx:
                current_predator_prob_map.put(MyAction.WEST, 0.5)

            if px > mx:
                current_predator_prob_map.put(MyAction.EAST, 0.5)

            if py > my:
                current_predator_prob_map.put(MyAction.NORTH, 0.5)

            if py < my:
                current_predator_prob_map.put(MyAction.SOUTH, 0.5)

        # Filter the actions which cannot be executed due to obstacles
        for obstacle in obstacles:
            if current_position.get_distance_to(obstacle) > 1:
                continue
            else:
                relative_obstacles_orientation = current_position.get_relative_orientation(obstacle)

                if relative_obstacles_orientation == GridRelativeOrientation.FRONT:
                    current_predator_prob_map.remove(MyAction.NORTH)
                    break
                elif relative_obstacles_orientation == GridRelativeOrientation.BACK:
                    current_predator_prob_map.remove(MyAction.SOUTH)
                    break
                elif relative_obstacles_orientation == GridRelativeOrientation.RIGHT:
                    current_predator_prob_map.remove(MyAction.EAST)
                    break
                else:
                    current_predator_prob_map.remove(MyAction.WEST)
                    break

        final_predator_action = None

        if len(current_predator_prob_map.list_actions()) > 0:
            final_predator_action = current_predator_prob_map.choice()

        return SocialAction(final_predator_action)


class MyEnvironment(HuntingEnvironment):
    """
    Your implementation of the environment in which cleaner agents work.
    """
    PREY_RANGE = 2
    PREDATOR_RANGE = 3

    def __init__(self, w, h, num_predators, num_prey):
        """
        Default constructor. This should call the initialize methods offered by the super class.
        """
        rand_seed = 42
        # rand_seed =  datetime.now()

        print("Seed = %i" % rand_seed)

        super(MyEnvironment, self).__init__()

        predators = []
        prey = []

        for i in range(num_predators):
            predators.append(MyPredator(map_width=w, map_height=h))

        for i in range(num_prey):
            prey.append(MyPrey())

        """ Message box for messages that need to be delivered by the environment to their respective recepients, on
        the next turn """
        self.message_box = []

        ## initialize the huniting environment
        self.initialize(w=w, h=h, predator_agents=predators, prey_agents=prey, rand_seed=rand_seed)

    def step(self):
        """
        This method should iterate through all agents, provide them provide them with perceptions, and apply the
        action they return.
        """
        """
        STAGE 1: generate perceptions for all agents, based on the state of the environment at the beginning of this
        turn
        """
        agent_perceptions = {}

        ## get perceptions for prey agents
        for prey_data in self._prey_agents:
            nearby_obstacles = self.get_nearby_obstacles(prey_data.grid_position, MyEnvironment.PREY_RANGE)
            nearby_predators = self.get_nearby_predators(prey_data.grid_position, MyEnvironment.PREY_RANGE)
            nearby_prey = self.get_nearby_prey(prey_data.grid_position, MyEnvironment.PREY_RANGE)

            predators = [(ag_data.linked_agent.id, ag_data.grid_position) for ag_data in nearby_predators]
            prey = [(ag_data.linked_agent.id, ag_data.grid_position) for ag_data in nearby_prey]

            agent_perceptions[prey_data] = MyAgentPerception(agent_position=prey_data.grid_position,
                                                             obstacles=nearby_obstacles,
                                                             nearby_predators=predators,
                                                             nearby_prey=prey)
            print("added")

        ## get perceptions for prey agents
        for predator_data in self._predator_agents:
            nearby_obstacles = self.get_nearby_obstacles(predator_data.grid_position, MyEnvironment.PREDATOR_RANGE)
            nearby_predators = self.get_nearby_predators(predator_data.grid_position, MyEnvironment.PREDATOR_RANGE)
            nearby_prey = self.get_nearby_prey(predator_data.grid_position, MyEnvironment.PREDATOR_RANGE)

            predators = [(ag_data.linked_agent.id, ag_data.grid_position) for ag_data in nearby_predators]
            prey = [(ag_data.linked_agent.id, ag_data.grid_position) for ag_data in nearby_prey]

            agent_perceptions[predator_data] = MyAgentPerception(agent_position=prey_data.grid_position,
                                                                 obstacles=nearby_obstacles,
                                                                 nearby_predators=predators,
                                                                 nearby_prey=prey,
                                                                 messages=self.message_box)

        ## TODO: create perceptions for predator agents, including messages in the `message_box`

        """
        STAGE 2: call response for each agent to obtain desired actions
        """

        pprint(agent_perceptions)

        agent_actions = {}
        ## TODO: get actions for all agents
        for prey_data in self._prey_agents:
            agent_actions[prey_data] = prey_data.linked_agent.response(agent_perceptions[prey_data])

        for predator_data in self._predator_agents:
            agent_actions[predator_data] = predator_data.linked_agent.response(agent_perceptions[predator_data])

        """
        STAGE 3: apply the agents' actions in the environment
        """
        for prey_data in self._prey_agents:
            if not prey_data in agent_actions:
                print("Agent %s did not opt for any action!" % str(prey_data))

            else:
                prey_action = agent_actions[prey_data]
                new_position = None

                if prey_action == MyAction.NORTH:
                    new_position = prey_data.grid_position.get_neighbour_position(GridOrientation.NORTH)
                elif prey_action == MyAction.SOUTH:
                    new_position = prey_data.grid_position.get_neighbour_position(GridOrientation.SOUTH)
                elif prey_action == MyAction.EAST:
                    new_position = prey_data.grid_position.get_neighbour_position(GridOrientation.EAST)
                elif prey_action == MyAction.WEST:
                    new_position = prey_data.grid_position.get_neighbour_position(GridOrientation.WEST)

                if not new_position in self._xtiles:
                    prey_data.grid_position = new_position
                else:
                    print("Agent %s tried to go through a wall!" % str(prey_data))

        for predator_data in self._predator_agents:
            if not predator_data in agent_actions:
                print("Agent %s did not opt for any action!" % str(predator_data))

            else:
                predator_action = agent_actions[predator_data]
                new_position = None
                ## TODO: handle case for a SocialAction instance

                if predator_action == MyAction.NORTH:
                    new_position = predator_data.grid_position.get_neighbour_position(GridOrientation.NORTH)
                elif predator_action == MyAction.SOUTH:
                    new_position = predator_data.grid_position.get_neighbour_position(GridOrientation.SOUTH)
                elif predator_action == MyAction.EAST:
                    new_position = predator_data.grid_position.get_neighbour_position(GridOrientation.EAST)
                elif predator_action == MyAction.WEST:
                    new_position = predator_data.grid_position.get_neighbour_position(GridOrientation.WEST)

                if not new_position in self._xtiles:
                    predator_data.grid_position = new_position
                else:
                    print("Agent %s tried to go through a wall!" % str(predator_data))

        """
        At the end of the turn remove the dead prey
        """
        self.remove_dead_prey()


class Tester(object):
    NUM_PREDATORS = 4
    NUM_PREY = 10

    WIDTH = 15
    HEIGHT = 10

    DELAY = 0.1

    def __init__(self):
        self.env = MyEnvironment(Tester.WIDTH, Tester.HEIGHT, Tester.NUM_PREDATORS, Tester.NUM_PREY)
        self.make_steps()

    def make_steps(self):
        while not self.env.goals_completed():
            self.env.step()

            # print(self.env)

            time.sleep(Tester.DELAY)


if __name__ == "__main__":
    tester = Tester()
    tester.make_steps()
