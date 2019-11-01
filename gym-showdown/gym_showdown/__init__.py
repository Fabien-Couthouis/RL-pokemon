from gym.envs.registration import register

register(
    id='showdown-v0',
    entry_point='gym_showdown.envs:ShowdownEnv',
)
register(
    id='showdown-extrahard-v0',
    entry_point='gym_showdown.envs:ShowdownExtraHardEnv',
)