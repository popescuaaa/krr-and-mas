from hide_and_seek.envs import HideAndSeekEnv, GameState, GameAction, Action, Reward
from hide_and_seek.envs import GridPosition, GridOrientation, GridRelativeOrientation
from random import choice
from time import sleep

class SimpleAgent:
    ag_ids = [1, 2]
    
    def __init__(self):
        self.total_reward = 0

    def get_action(self, state: GameState):
        return {ag_id: choice([e for e in Action]) for ag_id in SimpleAgent.ag_ids}


class DummyHider(SimpleAgent):
    pass


class DummySeeker(SimpleAgent):
    pass


class DeterministicSeeker(SimpleAgent):
    
    def __init__(self, env_width, env_height):
        super(DeterministicSeeker, self).__init__()
        self._env_width = env_width
        self._env_height = env_height
        
        self._tactical_pos = GridPosition(self._env_width, self._env_height - 2)
        self._final_pos = GridPosition(self._env_width - 2, self._env_height - 4)
        
        self._tactical_pos_reached = False
        self._final_pos_reached = False
        
    def get_action(self, state: GameState):
        act1 = Action.NOP
        act2 = Action.NOP

        # get seeker positions
        seeker1_pos = state.seeker_positions[1]
        seeker2_pos = state.seeker_positions[2]
        
        if not self._tactical_pos_reached:
            # if seekers are not in the tactical position move them there
            
            if seeker1_pos != self._tactical_pos:
                # seeker 1 takes the north route
                if seeker1_pos.x == 1 and seeker1_pos.y != self._env_height:
                    # if seeker 1 is on the left shaft, move NORTH
                    act1 = Action.NORTH
                elif seeker1_pos.y == self._env_height and seeker1_pos.x != self._env_width:
                    # if seeker 1 is on the top shaft, EAST
                    act1 = Action.EAST
                elif seeker1_pos.x == self._env_width and seeker1_pos != self._tactical_pos:
                    # if seeker 1 is on the right shaft, SOUTH
                    act1 = Action.SOUTH
                    
            if seeker2_pos != self._tactical_pos:
                # seeker 2 takes the south route
                if seeker2_pos.x == 1 and seeker2_pos.y != 1:
                    # if seeker 2 is on the left shaft, move NORTH
                    act2 = Action.SOUTH
                elif seeker2_pos.y == 1 and seeker2_pos.x != self._env_width:
                    # if seeker 2 is on the bottom shaft, move EAST
                    act2 = Action.EAST
                elif seeker2_pos.x == self._env_width and seeker2_pos != self._tactical_pos:
                    # if seeker 2 is on the right shaft, move NORTH
                    act2 = Action.NORTH
                    
            if seeker1_pos == self._tactical_pos and seeker2_pos == self._tactical_pos:
                self._tactical_pos_reached = True
        
        else:
            if not self._final_pos_reached:
                # when seeker 1 and seeker 2 have reached the tactical position, move to the final one in tandem
                if seeker1_pos.y == self._tactical_pos.y and seeker1_pos.x != 3:
                    act1 = Action.WEST
                    act2 = Action.WEST
                elif seeker1_pos.x == 3 and seeker1_pos.y != self._final_pos.y:
                    act1 = Action.SOUTH
                    act2 = Action.SOUTH
                elif seeker1_pos.y == self._final_pos.y and seeker1_pos.x != self._final_pos.x:
                    act1 = Action.EAST
                    act2 = Action.EAST
                else:
                    self._final_pos_reached = True
            else:
                # if the agent made it thus far and the game has not ended, just make them move randomly
                return super(DeterministicSeeker, self).get_action(state)
                
        return {1: act1, 2: act2}
        

if __name__ == "__main__":
    env = HideAndSeekEnv(max_turns=20)
    seeker_agent = DeterministicSeeker(env.w, env.h)
    hider_agent = DummyHider()
    
    turn = 0
    state = env.reset()
    
    print("## State at turn: %i\n" % turn)
    print(env)
    
    while True:
        turn += 1
        seeker_actions = seeker_agent.get_action(state)
        hider_actions = hider_agent.get_action(state)
        
        game_action = GameAction(seeker_actions=seeker_actions, hider_actions=hider_actions)
        state, reward, done = env.step(action=game_action)
        
        seeker_agent.total_reward += reward.total_seeker_reward
        hider_agent.total_reward += reward.total_hider_reward
        
        print("## Turn: %i" % turn)
        print("\tSeeker actions: %s " % str(game_action.seeker_actions))
        print("\tSeeker reward: %6.2f" % seeker_agent.total_reward)

        print("\tHider actions: %s " % str(game_action.hider_actions))
        print("\tHider reward: %6.2f" % hider_agent.total_reward)
        
        print(env)
        
        sleep(0.5)

        if done:
            break

