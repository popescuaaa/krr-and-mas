import numpy as np
from typing import Dict, Tuple, List
from enum import IntEnum


class Actions(IntEnum):
    LISTEN = 0
    LEFT = 1
    RIGHT = 2


class States(IntEnum):
    TL = 0    # Tiger: left
    TR = 1    # Tiger: right


class Obs(IntEnum):
    O_TL = 0  # Obs: Tiger left
    O_TR = 1  # Obs: Tiger right


class TigerEnv(object):
    def __init__(self, max_num_steps: int = 1, noise: float = 0.15):
        """
        Constructor

        Parameters
        ----------
        max_num_steps
            maximum number of steps allowed in the env
        noise
            observation noise. This means that with 1 - noise
            you hear the tiger behind the correct door.
        """
        self.max_num_steps = max_num_steps
        self.noise = noise
        self.num_steps = None
        self.__state = None
        self.done = True

        # define state mapping
        self.__num_states = 2
        self.__state_mapping = {
            States.TL: "Tiger left",
            States.TR: "Tiger right",
        }

        # define action mapping
        self.__num_actions = 3
        self.__action_mapping = {
            Actions.LISTEN: "Listen",
            Actions.LEFT: "Left",
            Actions.RIGHT: "Right",
        }

        # define observation mapping
        self.__num_obs = 2
        self.__obs_mapping = {
            Obs.O_TL: "Tiger Left",
            Obs.O_TR: "Tiger Right",
        }

        # init transitions & observations probabilities
        # and rewards
        self.__init_transitions()
        self.__init_observations()
        self.__init_rewards()

    def __init_transitions(self):
        # define transition probability for listening action
        #               Tiger: left      Tiger: right
        # Tiger: left    1.0              0.0
        # Tiger: right   0.0              1.0
        # This means that the tiger doesn't change location
        T_listen = np.array([[
            [1.0, 0.0],
            [0.0, 1.0]
        ]])

        # define transition probability for left action
        #               Tiger: left      Tiger: right
        # Tiger: left    0.5              0.5
        # Tiger: right   0.5              0.5
        # Resets the tiger location
        T_left = np.array([[
            [0.5, 0.5],
            [0.5, 0.5]
        ]])

        # define transition probability for the right action
        #               Tiger: left      Tiger: right
        # Tiger: left    0.5              0.5
        # Tiger: right   0.5              0.5
        # Resets the tiger location
        T_right = np.array([[
            [0.5, 0.5],
            [0.5, 0.5]
        ]])
        self.__T = np.concatenate([T_listen, T_left, T_right], axis=0)

    def __init_observations(self):
        # define observation probability for the listen action
        #                Obs: Tiger left    Obs: Tiger right
        # Tiger: left    0.85               0.15
        # Tiger: right   0.15               0.85
        O_listen = np.array([[
            [1 - self.noise, self.noise],
            [self.noise, 1 - self.noise]
        ]])

        # define observation probability for the left action
        #                Obs: Tiger left    Obs: Tiger right
        # Tiger: left    0.50               0.50
        # Tiger: right   0.50               0.50
        # Any observation without listening is informative
        O_left = np.array([[
            [0.5, 0.5],
            [0.5, 0.5]
        ]])

        # define observation probability for the right action
        #                Obs: Tiger left    Obs: Tiger right
        # Tiger: left    0.50               0.50
        # Tiger: right   0.50               0.50
        # Any observation without listening is informative
        O_right = np.array([[
            [0.5, 0.5],
            [0.5, 0.5],
        ]])

        self.__O = np.concatenate([O_listen, O_left, O_right], axis=0)

    def __init_rewards(self):
        # define rewards for listening
        # Tiger: left      -1
        # Tiger: right     -1
        # You get a -1 reward for listening
        R_listen = np.array([[-1, -1]])

        # define rewards for left action
        # Tiger: left      -100
        # Tiger: right      +10
        # If the tiger is left and you choose to go
        # left, then you get -100.
        # If the tiger is right and you choose to go
        # left, you get +10.
        R_left = np.array([[-100, +10]])

        # define rewards for right action
        # Tiger: left       +10
        # Tiger: right      -100
        # If the tiger is left and you choose to go
        # right, then you get +10
        # If the tiger is right and you choose to go
        # right, then you get -100.
        R_right = np.array([[+10, -100]])
        self.__R = np.concatenate([R_listen, R_left, R_right], axis=0)

    def reset(self):
        self.done = False
        self.num_steps = 0

        # initialize the state random
        # this puts the tiger behind the left and right
        # door with equal probability
        self.__state = np.random.choice([States.TL, States.TR])

    def step(self, action: Actions) -> Tuple[int, float, bool, Dict[str, int]]:
        """
        Performs an environment step

        Parameters
        ----------
        action
            action to be applied

        Returns
        -------
        Tuple containing the next observation, the reward,
        ending episode flag, other information.
        """
        assert not self.done, "The episode finished. Call reset()!"
        self.num_steps += 1
        self.done = (self.num_steps == self.max_num_steps)

        # get the next observation. this is stochastic
        obs = np.random.choice(
            a=[Obs.O_TL, Obs.O_TR],
            p=self.O[action][self.__state]
        )

        # get the reward. this is deterministic
        reward = self.R[action][self.__state]

        # get the next transition
        self.__state = np.random.choice(
            a=[States.TL, States.TR],
            p=self.T[action][self.__state]
        )

        # construct info
        info = {"num_steps": self.num_steps}
        return obs, reward, self.done, info

    @property
    def state_mapping(self) -> Dict[States, str]:
        """
        Returns
        -------
        State mapping (for display purpose)
        """
        return self.__state_mapping

    @property
    def action_mapping(self) -> Dict[Actions, str]:
        """
        Returns
        -------
        Action mapping (for display purposes)
        """
        return self.__action_mapping

    @property
    def obs_mapping(self) -> Dict[Obs, str]:
        """
        Returns
        -------
        Observation mapping (for display purposes)
        """
        return self.__obs_mapping

    @property
    def T(self) -> np.ndarray:
        """
        Returns
        -------
        Transition probability matrix.
        Axes: (a, s, s')
        """
        return self.__T

    @property
    def O(self) -> np.ndarray:
        """
        Returns
        -------
        Observation probability matrix.
        Axes: (a, s, o)
        """
        return self.__O

    @property
    def R(self) -> np.ndarray:
        """
        Returns
        -------
        Reward matrix:
        Axes: (a, s)
        """
        return self.__R

    @property
    def states(self) -> List[int]:
        """
        Returns
        -------
        List containing the states
        """
        return list(self.__state_mapping.keys())

    @property
    def actions(self) -> List[int]:
        """
        Returns
        -------
        List containing the actions
        """
        return list(self.__action_mapping.keys())

    @property
    def obs(self) -> List[int]:
        """
        Returns
        -------
        List containing the observations
        """
        return list(self.__obs_mapping.keys())