import gym
from gym import error, spaces, utils
from gym.utils import seeding
from .representation import *
from typing import Dict, List, Tuple, Optional


class Action(Enum):
    NORTH = (0, GridOrientation.NORTH, "N")
    EAST =  (1, GridOrientation.EAST, "E")
    SOUTH = (2, GridOrientation.SOUTH, "S")
    WEST =  (3, GridOrientation.WEST, "W")
    NOP =   (4, None, "Nop")
    
    def __init__(self, ordinal, orientation, display_string):
        self.ordinal = ordinal
        self.orientation = orientation
        self.display_string = display_string
    
    def __str__(self):
        return self.display_string

    
class GameAction:
    def __init__(self, seeker_actions: Dict[int, Action], hider_actions: Dict[int, Action]):
        self.seeker_actions = seeker_actions
        self.hider_actions = hider_actions
        
    def __eq__(self, other):
        if not isinstance(other, GameAction):
            return False
        
        for ag_id, ag_act in self.seeker_actions.items():
            if ag_act != other.seeker_actions[ag_id]:
                return False

        for ag_id, ag_act in self.hider_actions.items():
            if ag_act != other.hider_actions[ag_id]:
                return False
            
        return True
    
    def __hash__(self):
        res = 1

        for ag_act in self.seeker_actions.values():
            res *= hash(ag_act)

        for ag_act in self.hider_actions.values():
            res *= hash(ag_act)
        
        return res


class GameState:
    def __init__(self, seeker_positions: Dict[int, GridPosition],
                 hider_positions: Dict[int, GridPosition],
                 box_position: GridPosition):
        
        self.hider_positions = hider_positions
        self.seeker_positions = seeker_positions
        
        self.box_position = box_position
        
    def as_tuple(self):
        return tuple([self.seeker_positions[ag_id] for ag_id in sorted(self.seeker_positions.keys())] +
                     [self.hider_positions[ag_id] for ag_id in sorted(self.hider_positions.keys())] +
                     [self.box_position])
    
    def __eq__(self, other):
        if not isinstance(other, GameState):
            return False
        
        return self.as_tuple() == other.as_tuple()
    
    def __hash__(self):
        return hash(self.as_tuple())


class Reward:
    def __init__(self, seeker_rewards: Dict[int, float], hider_rewards: Dict[int, float]):
        self.hider_rewards = hider_rewards
        self.seeker_rewards = seeker_rewards
        self.total_seeker_reward = sum(seeker_rewards.values())
        self.total_hider_reward = sum(hider_rewards.values())


class HideAndSeekEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    
    MOVE_REWARD         = -0.5
    NOP_REWARD          = -0.5
    MOVE_BOX_REWARD     = 50
    GET_CAUGHT_REWARD   = -100
    HIDE_REWARD         = 100
    
    def __init__(self, w=6, h=7, max_turns=1000):
        """ Width and Height of the grid environment"""
        self.w = w
        self.h = h
        self.max_turns = max_turns
    
        """ A `GridPosition' record of all positions on the map, such as to provide reference """
        self._grid_positions = []
    
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
    
        """ Set of hide and seek agents populating the environment """
        self._seek_agent_pos = {}
        self._hide_agent_pos = {}
    
        self.turns = 0
        
        self.__initialize()
    
    def get_num_actions(self):
        return len(Action) * len(Action)
    
    
    def __initialize(self):
        """
        Initializes the environment with the provided width, height.
        Displays wall tiles around the environment and as an inner ring with one opening that can be covered by
        the box.
        :param w: width
        :param h: height
        """
        for i in range(0, self.w + 2):
          for j in range(0, self.h + 2):
            self._grid_positions.append(GridPosition(i, j))
    
        self._x0 = 0
        self._x1 = self.w + 1
    
        self._y0 = 0
        self._y1 = self.h + 1
    
        # generate walls
        for i in range(0, self.w + 2):
          self._xtiles.append(GridPosition(i, 0))
          self._xtiles.append((GridPosition(i, self._y1)))
    
        for j in range(0, self.h + 2):
          self._xtiles.append(GridPosition(0, j))
          self._xtiles.append((GridPosition(self._x1, j)))
    
        # generate inner ring
        self.rx_i0 = 2
        self.rx_i1 = self.w - 1
        self.ry_i0 = 2
        self.ry_i1 = self.h - 1
    
        for i in range(self.rx_i0, self.rx_i1 + 1):
          self._xtiles.append(GridPosition(i, self.ry_i0))
          self._xtiles.append((GridPosition(i, self.ry_i1)))
    
        for j in range(self.ry_i0 + 1, self.ry_i1):
          self._xtiles.append(GridPosition(self.rx_i0, j))
          if j != self.ry_i1 - 1:
            self._xtiles.append((GridPosition(self.rx_i1, j)))
    
        # set position of the box
        self._box_position: GridPosition = GridPosition(self.rx_i1 - 1, self.ry_i1 - 2)
    
        # set the positions of the agents
        # seekers share starting position
        self._seek_agent_pos = {
          1: GridPosition(self.rx_i0 - 1, self.ry_i0 + 1),
          2: GridPosition(self.rx_i0 - 1, self.ry_i0 + 1),
        }
        
        # hiders
        self._hide_agent_pos = {
          1: GridPosition(self.rx_i1 + 1, self.ry_i0),
          2: GridPosition(self.rx_i1 + 1, self.ry_i0 - 1),
        }
        
        # define the SAFE ZONE for the hider agents
        self._safe_zone = {
            "top_left": GridPosition(self.rx_i0 + 1, self.ry_i1 - 1),
            "bottom_right": GridPosition(self.rx_i1 - 1, self.ry_i0 + 1)
        }
        
        # define doorway into SAFE ZONE
        self._doorway_pos: GridPosition = GridPosition(self.rx_i1, self.ry_i1 - 1)
        self._box_blocking_pos: GridPosition = GridPosition(self.rx_i1 - 1, self.ry_i1 - 1)
    
    def _get_all_neighbours(self, pos: GridPosition) -> List[GridPosition]:
        """
        Returns all the surrounding 8 neighbour positions of this GridPosition, if they do not surpass the grid
        :return: The List of neighbour GridPositions
        """
        neighbours = []
        for dx, dy in zip([-1, 0, 1], [-1, 0, 1]):
            if dx != 0 or dy != 0:
                nx = pos.x + dx
                ny = pos.y + dy
                if nx >= 0 and nx <= self.w and ny >=0 and ny <= self.h:
                    neighbours.append(GridPosition(nx, ny))
        
        return neighbours
    
    def _any_hider_found(self):
        """
        Check if any hider agents were found by the seekers
        :return: True if at least one hider is found, False otherwise
        """
        for hider_id, hider_pos in self._hide_agent_pos.items():
            for seeker_id, seeker_pos in self._seek_agent_pos.items():
                
                if seeker_pos.is_neighbour(hider_pos):
                    return True
        
        return False
    
    def _is_hider_safe(self, hider_pos):
        if hider_pos.get_relative_dx(self._safe_zone["top_left"]) < 0:
            return False
        if hider_pos.get_relative_dx(self._safe_zone["bottom_right"]) > 0:
            return False
        if hider_pos.get_relative_dy(self._safe_zone["top_left"]) > 0:
            return False
        if hider_pos.get_relative_dy(self._safe_zone["bottom_right"]) < 0:
            return False
        if hider_pos.is_neighbour(self._doorway_pos):
            return False
        
        return True
    
    def _all_hiders_safe(self):
        return self._box_position == GridPosition(self.rx_i1 - 1, self.ry_i1 - 1) and \
            all([self._is_hider_safe(hider_pos) for hider_pos in self._hide_agent_pos.values()])
            
    def _game_finished(self):
        """
        Return True if the seeker agents found at least one hider OR if the hider agents managed
        to secure their presence in the safe zone AND lock the entrance with the box
        :return:
        """
        if self.turns >= self.max_turns:
            return True
        
        if self._any_hider_found():
            return True
        
        # check if box is in blocking position
        if self._box_position == GridPosition(self.rx_i1 - 1, self.ry_i1 - 1):
            # check if all hiders are safe
            if all([self._is_hider_safe(hider_pos) for _, hider_pos in self._hide_agent_pos.items()]):
                return True
        
        return False
    
    def _hiders_in_same_spot(self) -> Optional[GridPosition]:
        hiders_spot = None
        for hider_id, hider_pos in self._hide_agent_pos.items():
            if not hiders_spot:
                hiders_spot = hider_pos
            elif hider_pos != hiders_spot:
                return None
        
        return hiders_spot
    
    def _hiders_have_same_action(self, action: GameAction) -> Optional[Action]:
        hiders_action = None
        for id, act in action.hider_actions.items():
            if not hiders_action:
                hiders_action = act
            elif act != hiders_action:
                return None
            
        return hiders_action
    
    def _get_observations(self) -> Tuple[Dict[int, List[GridRelativeOrientation]],
                                         Dict[int, List[GridRelativeOrientation]]]:
        seeker_obstacles = {ag_id: [] for ag_id in self._seek_agent_pos}
        hider_obstacles = {ag_id: [] for ag_id in self._hide_agent_pos}
    
        for ag_id, ag_pos in self._seek_agent_pos.items():
            neighbour_obstacles = [ag_pos.get_simple_relative_orientation(pos)
                                   for pos in self._get_all_neighbours(ag_pos) if pos in self._xtiles]
            seeker_obstacles[ag_id] = neighbour_obstacles
    
        for ag_id, ag_pos in self._hide_agent_pos.items():
            neighbour_obstacles = [ag_pos.get_simple_relative_orientation(pos)
                                   for pos in self._get_all_neighbours(ag_pos) if pos in self._xtiles]
            hider_obstacles[ag_id] = neighbour_obstacles
            
        return seeker_obstacles, hider_obstacles
    
    def _get_state(self):
        seeker_positions = {ag_id: ag_pos for ag_id, ag_pos in self._seek_agent_pos.items()}
        hider_positions = {ag_id: ag_pos for ag_id, ag_pos in self._hide_agent_pos.items()}
    
        return GameState(seeker_positions, hider_positions, self._box_position.clone())
    
    def step(self, action: GameAction) -> Tuple[GameState, Reward, bool]:
        seeker_rewards = {seeker_id : 0 for seeker_id in self._seek_agent_pos}
        hider_rewards = {hider_id: 0 for hider_id in self._hide_agent_pos}
        
        # SEEKER ACTIONS AND REWARDS
        for seeker_id, seeker_pos in self._seek_agent_pos.items():
            seeker_act = action.seeker_actions[seeker_id]
            
            new_pos = seeker_pos.get_neighbour_position(seeker_act.orientation)
            if new_pos not in self._xtiles and new_pos != self._box_position:
                self._seek_agent_pos[seeker_id] = new_pos
            
            seeker_rewards[seeker_id] += HideAndSeekEnv.MOVE_REWARD
        
        # HIDER ACTIONS AND REWARDS
        hider_same_spot = self._hiders_in_same_spot()
        if hider_same_spot:
            hiders_same_action = self._hiders_have_same_action(action)
            if hiders_same_action:
                new_pos = hider_same_spot.get_neighbour_position(hiders_same_action.orientation)
                
                if new_pos == self._box_position:
                    new_box_pos = self._box_position.get_neighbour_position(hiders_same_action.orientation)
                    if new_box_pos not in self._xtiles and new_box_pos not in self._seek_agent_pos.values():
                        # if the agents want to move the box and the box can actually be moved,
                        # then update agent and box positions
                        for hider_id in self._hide_agent_pos:
                            # only update the box position here, the agent pos will get updated in the general case
                            self._box_position = new_box_pos
                            
                            # if the box is moved into the position blocking the entrance,
                            # both hiders get half the MOVE BOX reward
                            if self._box_position == self._box_blocking_pos:
                                hider_rewards[hider_id] += HideAndSeekEnv.MOVE_BOX_REWARD / 2
        
        # if they are not in the same spot OR they are BUT perform different movements, just add the movement reward
        for hider_id, hider_pos in self._hide_agent_pos.items():
            hider_act = action.hider_actions[hider_id]
    
            new_pos = hider_pos.get_neighbour_position(hider_act.orientation)
            if new_pos not in self._xtiles and new_pos != self._box_position:
                self._hide_agent_pos[hider_id] = new_pos
    
            hider_rewards[hider_id] += HideAndSeekEnv.MOVE_REWARD
        
        # check if hiders are safe and give appropriate reward
        if self._all_hiders_safe():
            for hider_id in self._hide_agent_pos:
                hider_rewards[hider_id] += HideAndSeekEnv.HIDE_REWARD / 2
                
        # check if hiders were found and give appropriate reward
        if self._any_hider_found():
            for hider_id in self._hide_agent_pos:
                hider_rewards[hider_id] += HideAndSeekEnv.GET_CAUGHT_REWARD / 2
            
            for seeker_id in self._seek_agent_pos:
                seeker_rewards[seeker_id] += (-1) * HideAndSeekEnv.GET_CAUGHT_REWARD / 2
        
        self.turns += 1
        return self._get_state(), Reward(seeker_rewards, hider_rewards), self._game_finished()
        
        
    def reset(self) -> GameState:
        # reset turns counter
        self.turns = 0

        # set position of the box
        self._box_position: GridPosition = GridPosition(self.rx_i1 - 1, self.ry_i1 - 2)

        # set the positions of the agents
        # seekers share starting position
        self._seek_agent_pos = {
            1: GridPosition(self.rx_i0 - 1, self.ry_i0 + 1),
            2: GridPosition(self.rx_i0 - 1, self.ry_i0 + 1),
        }

        # hiders
        self._hide_agent_pos = {
            1: GridPosition(self.rx_i1 + 1, self.ry_i0),
            2: GridPosition(self.rx_i1 + 1, self.ry_i0 - 1),
        }
        
        return self._get_state()
        
  
    def render(self, mode='human'):
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
            for agent_id in self._seek_agent_pos:
              if self._seek_agent_pos[agent_id] == pos:
                agent_string += str("S%i" % agent_id)
    
            for agent_id in self._hide_agent_pos:
              if self._hide_agent_pos[agent_id] == pos:
                agent_string += str("H%i" % agent_id)
    
            k = 0
            if pos in self._xtiles:
              while k < self._cellW:
                res += "X"
                k += 1
    
            if pos == self._box_position:
              while k < self._cellW:
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
              elif pos == self._box_position:
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
  
    def close(self):
        pass
  
    def __str__(self):
        return self.render()
