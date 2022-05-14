from enum import Enum
from typing import List

class GridRelativeOrientation(Enum):
    """
    Implementation for orthogonal and diagonal relative orientations in a rectangular grid.
    """
    FRONT = 0
    FRONT_RIGHT = 1
    RIGHT = 2
    BACK_RIGHT = 3
    BACK = 4
    BACK_LEFT = 5
    LEFT = 6
    FRONT_LEFT = 7

class GridOrientation(Enum):
    NORTH = (0, 0, 1, "^")
    EAST = (1, 1, 0, ">")
    SOUTH = (2, 0, -1, "v")
    WEST = (3, -1, 0, "<")

    def __init__(self, ordinal, dx, dy, display_string):
        self.ordinal = ordinal
        self.dx = dx
        self.dy = dy
        self.display_string = display_string

    def __str__(self):
        return self.display_string

    # NORTH = Orientation(1, 0, 1,    "^")
    # EAST = Orientation(2, 1, 0,     ">")
    # SOUTH = Orientation(3, 0, -1,   "v")
    # WEST = Orientation(4, -1, 0,    "<")


    def compute_relative_orientation(self, relative_orientation):
        """
        Computes the absolute orientation that is at the specified orientation relative to `this'.
        E.g. if the current orientation is SOUTH and the relative orientation is RIGHT, the result is WEST.
        :param relative_orientation: the GridRelativeOrientation value
        :return: the resulting GridOrientation instance
        """
        angle = relative_orientation.value
        is_half_angle = (angle % 2) != 0
        if is_half_angle:
            raise ValueError("the relative orientation must be a straight angle")

        straight_angle = angle // 2
        return list(GridOrientation)[(self.ordinal + straight_angle) % 4]

    def get_relative_dx(self, relative):
        """
        Returns the delta x for the position at the indicated orientation, relative to <code>this</code> orientation.
        E.g. if the orientation is EAST, and the relative orientation is BACK-RIGHT, the resulting orientation is
        SOUTH-WEST, with a delta x of -1 and a delta y of -1.
        :param relative: the relative orientation
        :return: the delta x of the position at that relative orientation.
        """
        angle = relative.value
        straight_angle = angle // 2
        is_half_angle = angle % 2

        straight_result = (self.ordinal + straight_angle) % 4

        res = list(GridOrientation)[straight_result].dx
        if is_half_angle:
            res += list(GridOrientation)[(straight_result + 1) % 4].dx

        return res


    def get_relative_dy(self, relative):
        """
        Returns the delta y for the position at the indicated orientation, relative to <code>this</code> orientation.
        E.g. if the orientation is EAST, and the relative orientation is BACK-RIGHT, the resulting orientation is
        SOUTH-WEST, with a delta x of -1 and a delta y of -1.
        :param relative: the relative orientation
        :return: the delta y of the position at that relative orientation.
        """
        angle = relative.value
        straight_angle = angle // 2
        is_half_angle = angle % 2

        straight_result = (self.ordinal + straight_angle) % 4

        res = list(GridOrientation)[straight_result].dy
        if is_half_angle:
            res += list(GridOrientation)[(straight_result + 1) % 4].dy

        return res


class GridPosition(object):
    """
    Implementation for positions in a rectangular grid.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.x == other.x and self.y == other.y
        else:
            return False

    def __hash__(self):
        return self.x + self.y

    def __str__(self):
        return "(%i, %i)" % (self.x, self.y)
  
    def clone(self):
        return GridPosition(self.x, self.y)
    
    def get_neighbour_position(self, direction, relative_orientation = GridRelativeOrientation.FRONT):
        """
        Returns the position that is one of the 8 (orthogonal and diagonal) neighbors of <code>this</code> and is in a
        direction that has the provided orientation relative to the provided direction.
        :param direction: direction used to compute the neighbor position, as an `GridOrientation' instance.
        :param relative_orientation: orientation of the returned position, relative to the direction
        in the first argument. The default relative orientation is FRONT, which means the function will compute the
        neighbour cell that is in the "direction" specified by :arg direction.
        E.g. if direction is NORTH, the returned position will be north of this, relative to the grid.
        If it is WEST, the returned position will be west of this, relative to the grid.
        :return: the neighbor `GridPosition'
        """
        if direction:
            return GridPosition(self.x + direction.get_relative_dx(relative_orientation),
                                self.y + direction.get_relative_dy(relative_orientation))
        
        return GridPosition(self.x, self.y)
    
    def is_neighbour(self, grid_position):
        """
        Indicates whether the provided position is a neighbor (orthogonal or diagonal).
        :param grid_position: the candidate `GridPosition' neighbour
        :return: True if the candidate is a neighbour
        """
        return abs(self.x - grid_position.x) <= 1 and abs(self.y - grid_position.y) <= 1


    def is_neighbour_ortho(self, grid_position):
        """
        Indicates whether the provided position is an orthogonal neighbor (north, south, east or west).
        :param grid_position: the candidate neighbor.
        :return: True if the candidate is a neighbour
        """
        return (abs(self.x - grid_position.x) == 1 and self.y == grid_position.y) or \
               (self.x == grid_position.x and abs(self.y - grid_position.y) == 1)


    def get_simple_relative_orientation(self, other_position):
        """
        Determines the relative orientation of another GridPosition with respect to `this'.
        :param other_position: The position for which the relative orientation needs to be determined.
        :return: The `GridRelativeOrientation' of `otherPosition' with respect to the current one.
        """
        delta_x = other_position.x - self.x
        if delta_x < 0:
            delta_x = -1
        elif delta_x > 0:
            delta_x = 1

        delta_y = other_position.y - self.y
        if delta_y < 0:
            delta_y = -1
        elif delta_y > 0:
            delta_y = 1

        if delta_x == 0:
            if delta_y >= 0:
                return GridRelativeOrientation.FRONT
            return GridRelativeOrientation.BACK
        elif delta_x > 0:
            if delta_y > 0:
                return  GridRelativeOrientation.FRONT_RIGHT
            elif delta_y < 0:
                return GridRelativeOrientation.BACK_RIGHT
            else:
                return GridRelativeOrientation.RIGHT
        else:
            if delta_y > 0:
                return GridRelativeOrientation.FRONT_LEFT
            elif delta_y < 0:
                return GridRelativeOrientation.BACK_LEFT
            else:
                return GridRelativeOrientation.LEFT


    def get_relative_orientation(self, reference_orientation, neighbour_position):
        """
        Returns the relative orientation of a position relative to `this' position and a reference
        orientation.
        E.g. for a `GridOrientation' reference_orientation of EAST, an orthogonal `GridPosition' neighbor position to
        the right of this position will be in FRONT.
        :param reference_orientation: the absolute orientation which is considered as 'front', or 'forward'.
        :param neighbour_position: the position for which to compute the relative orientation.
        :return: the relative orientation.
        """
        if not self.is_neighbour(neighbour_position):
            raise ValueError("Given position is not a neighbor")

        for orientation in list(GridRelativeOrientation):
            if self.get_neighbour_position(reference_orientation, orientation) == neighbour_position:
                return orientation

        raise RuntimeError("Should not be here!")
    

    def get_distance_to(self, grid_position):
        """
        Computes the Manhatten distance from a specified position
        :param grid_position: the other `GridPosition' position
        :return: the distance
        """
        return abs(self.x - grid_position.x) + abs(self.y - grid_position.y)

    def get_relative_dx(self, grid_position):
        return self.x - grid_position.x
    
    def get_relative_dy(self, grid_position):
        return self.y - grid_position.y

    def is_x_even(self):
        """
        :return: True if the x coordinate is even
        """
        return abs(self.x) % 2 == 0

    def is_y_event(self):
        """
        :return: True if the y coordinate is even
        """
        return abs(self.y) % 2 == 0


if __name__ == "__main__":
    pos = GridPosition(1, 1)

    print(pos.get_neighbour_position(GridOrientation.NORTH))
    print(pos.get_neighbour_position(GridOrientation.EAST))
    print(pos.get_neighbour_position(GridOrientation.WEST))
    print(pos.get_neighbour_position(GridOrientation.SOUTH))

    print("===========")
    print(pos.get_neighbour_position(GridOrientation.SOUTH, GridRelativeOrientation.FRONT))
    print(pos.get_neighbour_position(GridOrientation.SOUTH, GridRelativeOrientation.FRONT_LEFT))
    print(pos.get_neighbour_position(GridOrientation.SOUTH, GridRelativeOrientation.FRONT_RIGHT))
    print(pos.get_neighbour_position(GridOrientation.SOUTH, GridRelativeOrientation.BACK))
    print(pos.get_neighbour_position(GridOrientation.SOUTH, GridRelativeOrientation.BACK_LEFT))
    print(pos.get_neighbour_position(GridOrientation.SOUTH, GridRelativeOrientation.BACK_RIGHT))

