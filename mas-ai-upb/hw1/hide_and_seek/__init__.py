from gym.envs.registration import register

register(
    id='hide-and-seek-v0',
    entry_point='hide_and_seek.envs:HideAndSeekEnv',
)