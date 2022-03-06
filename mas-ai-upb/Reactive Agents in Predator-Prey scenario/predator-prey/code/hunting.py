from gridworld import *


class WildLifeAgent(Agent):
    """
    Parent class for agents in the predator-prey scenario.
    """
    agent_counter = 0

    def __init__(self, agent_type):
        """
        Default constructor for WildLifeAgent
        :param agent_type: the agent type, whether Predator or Prey
        """
        self.agent_type = agent_type

        ## Initialize the unique numeric ID of the agent
        self.id = WildLifeAgent.agent_counter

        ## Increase global counter
        WildLifeAgent.agent_counter += 1


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
        return "%s%i" % ("H" if self.agent_type == WildLifeAgentData.PREDATOR else "F", self.id)


class WildLifeAgentData(GridAgentData):
    PREDATOR = 1
    PREY = 2

    def __init__(self, linked_agent, agent_type, grid_position):
        super(WildLifeAgentData, self).__init__(linked_agent, grid_position, GridOrientation.NORTH)

        """The type of wildlife agent: predator or prey"""
        self.agent_type = agent_type


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.agent_type == other.agent_type and self.grid_position == other.grid_position and \
                self.linked_agent == other.linked_agent
        else:
            return False


    def __hash__(self):
        return self.linked_agent.id


    def __str__(self):
        return str(self.linked_agent)


class HuntingEnvironment(AbstractGridEnvironment):

    def __init__(self):
        super(HuntingEnvironment, self).__init__()

        self._predator_agents = []
        self._prey_agents = []


    def add_agent(self, agent_data):
        self.__add_wildlife_agent(agent_data)


    def __add_wildlife_agent(self, agent_data):
        if agent_data.agent_type == WildLifeAgentData.PREDATOR:
            self._predator_agents.append(agent_data)

        elif agent_data.agent_type == WildLifeAgentData.PREY:
            self._prey_agents.append(agent_data)

        else:
            raise ValueError("Illegal type of wildlife agent: %s" % str(agent_data.linked_agent))

        self._agents.append(agent_data)


    def initialize(self, w, h, predator_agents, prey_agents, rand_seed = None):
        """
        Initializes the environment with the provided width, height and number of predator and prey agents.
        :param w: width of the grid
        :param h: height of the grid
        :param predator_agents: list of predator agents to place on the grid
        :param prey_agents: list of prey agents to place on the grid
        :param rand_seed: Seed for random number generator. May be None
        """

        num_predators = len(predator_agents)
        num_prey = len(prey_agents)

        ## generate grid positions
        for i in range(0, w + 2):
            for j in range(0, h + 2):
                self._grid_positions.append(GridPosition(i, j))

        self._x0 = 0
        self._x1 = w + 1

        self._y0 = 0
        self._y1 = h + 1

        ## Generate all wall x-tiles
        for i in range(0, w + 2):
            self._xtiles.append(GridPosition(i, 0))
            self._xtiles.append((GridPosition(i, self._y1)))

        for j in range(0, h + 2):
            self._xtiles.append(GridPosition(0, j))
            self._xtiles.append((GridPosition(self._x1, j)))

        ## generate all predators
        attempts = 10 * num_predators * num_predators
        generated = 0

        if rand_seed:
            random.seed(rand_seed)

        while attempts > 0 and generated < num_predators:
            x = random.randint(1, w)
            y = random.randint(1, h)

            pos = GridPosition(x, y)
            ok = True

            for predator_data in self._predator_agents:
                if pos.get_distance_to(predator_data.grid_position) <= 1:
                    ok = False

            if ok:
                generated += 1
                self.__add_wildlife_agent(WildLifeAgentData(predator_agents.pop(),
                                                            agent_type=WildLifeAgentData.PREDATOR, grid_position=pos))

            attempts -= 1

        if generated < num_predators:
            print("Failed to generate all required predator agents. Wanted: %i, generated: %i" % (num_predators, generated))


        ## generate all prey
        attempts = 10 * num_prey * num_prey
        generated = 0

        while attempts > 0 and generated < num_prey:
            x = random.randint(1, w)
            y = random.randint(1, h)

            pos = GridPosition(x, y)
            ok = True

            for predator_data in self._predator_agents:
                if pos.get_distance_to(predator_data.grid_position) <= 2:
                    ok = False

            for prey_data in self._prey_agents:
                if pos.get_distance_to(prey_data.grid_position) <= 1:
                    ok = False

            if ok:
                generated += 1
                self.__add_wildlife_agent(WildLifeAgentData(prey_agents.pop(), agent_type=WildLifeAgentData.PREY,
                                                            grid_position=pos))

            attempts -= 1

        if generated < num_prey:
            print("Failed to generate all required prey agents. Wanted: %i, generated: %i" % (num_prey, generated))


    def remove_prey_agent(self, prey_data):
        """
        Remove a prey agent.
        :param prey_data: the agent to remove, as a reference to its corresponding `WildlifeAgentData' instance
        """
        self._prey_agents.remove(prey_data)
        self._agents.remove(prey_data)


    def get_nearby_obstacles(self, grid_position, range):
        """
        Returns the set of obstacles which are at a distance from a given position by at most `range'
        :param grid_position: the position of the agent
        :param range: the range the agent can observe
        :return: The set of GridPositions where obstacles are found
        """
        nearby_obstacles = []

        for pos in self._xtiles:
            if pos.get_distance_to(grid_position) <= range:
                nearby_obstacles.append(pos)

        return nearby_obstacles


    def get_nearby_predators(self, grid_position, range):
        """
        Returns the set of predator agents which are at a distance from a given position by at most `range'.
        :param grid_position: Position around which to determine the nearby agents
        :param range: the range the agent can observe
        :return: The set of nearby predator agents given as `WildlifeAgentData' instances.
        """
        nearby_agents = []
        for predator_data in self._predator_agents:
            if grid_position.get_distance_to(predator_data.grid_position) <= range:
                nearby_agents.append(predator_data)

        return nearby_agents


    def get_nearby_prey(self, grid_position, range):
        """
        Returns the set of prey agents which are at a distance from a given position by at most `range'.
        :param grid_position: Position around which to determine the nearby agents
        :param range: the range the agent can observe
        :return: The set of nearby prey agents given as `WildlifeAgentData' instances.
        """
        nearby_agents = []
        for prey_data in self._prey_agents:
            if grid_position.get_distance_to(prey_data.grid_position) <= range:
                nearby_agents.append(prey_data)

        return nearby_agents


    def __is_dead_prey(self, prey_data):
        """
        Check if prey agent is dead
        :param prey_data: the prey agent given as WildlifeAgentData instance for which to check conditions for
        being dead
        :return: True if agent is dead, False otherwise
        """
        has_neighbour_predator = False
        num_close_predators = 0

        prey_pos = prey_data.grid_position
        predators = []

        for predator_data in self._predator_agents:
            predator_dist = predator_data.grid_position.get_distance_to(prey_pos)

            if predator_dist <= 2:
                has_neighbour_predator = True
                predators = [str(predator_data.linked_agent)]

            elif predator_dist <= 2:
                num_close_predators += 1
                predators.append(str(predator_data.linked_agent))

                if num_close_predators >= 2:
                    break

        if has_neighbour_predator or num_close_predators >= 2:
            print("Prey %s is dead, killed by %s" % (str(prey_data.linked_agent), ", ".join(predators)))
            return True

        return False


    def remove_dead_prey(self):
        """
        Remove dead prey. The condition for a prey being killed is that there be either one predator at a Manhattan
        distance of 1, or at least two predators, each at a Manhattan distance of 2 or less from the prey
        :return:
        """
        self._prey_agents[:] = [prey_data for prey_data in self._prey_agents if not self.__is_dead_prey(prey_data)]
        self._agents[:] = [ag_data for ag_data in self._agents if ag_data.agent_type == WildLifeAgentData.PREDATOR or
                           not self.__is_dead_prey(ag_data)]


    def goals_completed(self):
        return not self._prey_agents


    def __str__(self):
        res = ""
        res += "  |"

        ## border top
        for i in range(self._x0, self._x1 + 1):
            step = 1
            if i >= 10:
                step = 2

            for k in range(0, self._cellW - step):
                res += " "

            res += str(i) + "|"

        res += "\n"
        res += "--+"

        for i in range(self._x0, self._x1 + 1):
            for k in range(0, self._cellW):
                res += "-"
            res += "+"

        res += "\n"

        ## for each line
        for j in range(self._y1, self._y0 - 1, -1):
            # first cell row
            if j < 10:
                res += " " + str(j) + "|"
            else:
                res += str(j) + "|"

            for i in range(self._x0, self._x1 + 1):
                pos = GridPosition(i, j)
                agent_string = ""
                for agent_data in self._agents:
                    if agent_data.grid_position == pos:
                        agent_string += str(agent_data.linked_agent)

                k = 0
                if pos in self._xtiles:
                    while k < self._cellW:
                        res += "X"
                        k += 1

                if self._cellH < 2 and pos in self._jtiles:
                    res += "~"
                    k += 1

                if len(agent_string) > 0:
                    if self._cellW == 1:
                        if len(agent_string) > 1:
                            res += "."
                        else:
                            res += agent_string
                        k += 1
                    else:
                        res += agent_string[:min(len(agent_string), self._cellW - k)]
                        k += min(len(agent_string), self._cellW - k)

                while k < self._cellW:
                    res += " "
                    k += 1

                res += "|"

            res += "\n"

            # second cell row
            res += "  |"
            for i in range(self._x0, self._x1 + 1):
                pos = GridPosition(i, j)
                for k in range(0, self._cellW):
                    if pos in self._xtiles:
                        res += "X"
                    elif pos in self._jtiles:
                        res += "~"
                    else:
                        res += " "
                res += "|"

            res += "\n"

            # other cell rows
            for ky in range(0, self._cellH - 2):
                res += "|"
                for i in range(self._x0, self._x1 + 1):
                    for k in range(0, self._cellW):
                        if GridPosition(i, j) in self._xtiles:
                            res += "X"
                        else:
                            res += " "
                    res += "|"
                res += "\n"

            res += "--+"

            for i in range(self._x0, self._x1 + 1):
                for k in range(0, self._cellW):
                    res += "-"
                res += "+"
            res += "\n"

        return res