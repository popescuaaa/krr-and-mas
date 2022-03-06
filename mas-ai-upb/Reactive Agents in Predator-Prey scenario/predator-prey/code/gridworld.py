from base import *
from representation import *
import random
from copy import deepcopy

class GridAgentData(AgentData):
    def __init__(self, linked_agent, grid_position, current_orientation):
        """
        :param linked_agent: the agent
        :param grid_position: the position on the grid
        :param current_orientation: the orientation on the grid
        """
        super(GridAgentData, self).__init__(linked_agent)

        self.grid_position = grid_position
        self.current_orientation = current_orientation

        """
        The number of points gathered by the agent
        """
        self.points = 0


    def add_points(self, delta):
        """
        :param delta: number of points to add; may be negative
        """
        self.points += delta


class NearbyAgent(object):
    """
    Structure storing information about a nearby agent.
    """

    def __init__(self, relative_orientation, is_cognitive, agent_points):
        """
        Creates a new structure indicating information about a nearby agent.
        :param relative_orientation: The GridRelativeOrientation orientation relative to `this' agent
        :param is_cognitive: is the neighbour agent cognitive?
        :param agent_points: the points gathered by the neighbour agent
        """
        self.relative_orientation = relative_orientation
        self.is_cognitive = is_cognitive
        self.agent_points = agent_points





class AbstractGridEnvironment(Environment):

    def __init__(self):
        super(AbstractGridEnvironment, self).__init__()


        """ A `GridPosition' record of all positions on the map, such as to provide reference """
        self._grid_positions = []

        """ Set of junk tile `GridPosition' positions """
        self._jtiles = []

        """ Set of wall tile `GridPosition' positions """
        self._xtiles = []

        """ Min and max values for the corners of the grid environment """
        self._x0 = 0
        self._x1 = 0
        self._y0 = 0
        self._y1 = 0

        """ Width and height of grid cells for display purposes """
        self._cellW = 2
        self._cellH = 2

        """ Set of `GridAgentData' agents populating the environment """
        self._agents = []


    def goals_completed(self):
        return not self._jtiles


    def add_agent(self, agent_data):
        self._agents.append(agent_data)


    def initialize(self, w, h, nr_jtiles, nr_xtiles, rand_seed = None):
        """
        Initializes the environment with the provided width, height and number of J- and X-tiles.
        :param w: width
        :param h: height
        :param nr_jtiles: number of junk tiles
        :param nr_xtiles: number of x tiles
        :param rand_seed: random number generator seed used in generation process, can be None
        """
        for i in range(0, w + 2):
            for j in range(0, h + 2):
                self._grid_positions.append(GridPosition(i, j))

        self._x0 = 0
        self._x1 = w + 1

        self._y0 = 0
        self._y1 = h + 1


        for i in range(0, w + 2):
            self._xtiles.append(GridPosition(i, 0))
            self._xtiles.append((GridPosition(i, self._y1)))

        for j in range(0, h + 2):
            self._xtiles.append(GridPosition(0, j))
            self._xtiles.append((GridPosition(self._x1, j)))

        ## generate rest of X tiles
        attempts = 10 * nr_xtiles * nr_xtiles
        generated = 0

        if rand_seed:
            random.seed(rand_seed)

        while attempts > 0 and generated < nr_xtiles:
            x = random.randint(1, w)
            y = random.randint(1, h)

            pos = GridPosition(x, y)
            ok = True

            for grid_pos in self._xtiles:
                if pos.get_distance_to(grid_pos) <= 2:
                    ok = False

            if ok:
                generated += 1
                self._xtiles.append(pos)

            attempts -= 1

        if generated < nr_xtiles:
            print("Failed to generate all required X-tiles. Wanted: %i, generated: %i" % (nr_xtiles, generated))


        ## generate all J tiles
        attempts = 10 * nr_jtiles * nr_jtiles
        generated = 0

        while attempts > 0 and generated < nr_jtiles:
            x = random.randint(1, w)
            y = random.randint(1, h)

            pos = GridPosition(x, y)

            if not pos in self._jtiles and not pos in self._xtiles:
                generated += 1
                self._jtiles.append(pos)

            attempts -= 1

        if generated < nr_jtiles:
            print("Failed to generate all required J-tiles. Wanted: %i, generated: %i" % (nr_jtiles, generated))



    def clean_tile(self, grid_position):
        """
        Removes a position from the list of dirty tiles.
        :param grid_position: the J tile to remove
        """
        if not grid_position in self._jtiles:
            raise ValueError("GridPosition was not dirty")

        self._jtiles.remove(grid_position)


    def _get_positions(self):
        return deepcopy(self._grid_positions)

    def _get_x_tiles(self):
        return deepcopy(self._xtiles)

    def _get_j_tiles(self):
        return deepcopy(self._jtiles)


    def get_bottom_left(self):
        return GridPosition(self._x0 + 1, self._y0 + 1)

    def get_top_left(self):
        return GridPosition(self._x0 + 1, self._y1 - 1)

    def get_bottom_right(self):
        return GridPosition(self._x1 - 1, self._y0 + 1)

    def get_top_right(self):
        return GridPosition(self._x1 - 1, self._y1 - 1)


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
                        agent_string += str(agent_data.current_orientation) + str(agent_data.linked_agent)

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


# if __name__ == "__main__":
#     env = AbstractGridEnvironment()
#     env.initialize(10, 10, 3, 3)
#
#     print(env)