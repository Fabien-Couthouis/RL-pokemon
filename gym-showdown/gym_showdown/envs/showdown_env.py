import gym
from gym import error, spaces, utils
from gym.utils import seeding

try:
    from showdown_client.client import *
except ImportError as e:
    raise error.DependencyNotInstalled(f"{e} \n Error: missing dependency showdown_client")


class ShowdownEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        try:
            with open('data/login.txt', 'rt') as f,\
                    open('data/team.txt', 'rt') as team:
                team = team.read()
                username, password = f.read().strip().splitlines()
        self.client = Client(name=username, password=password)
        self.action_space = spaces.Discrete(4)
    
    def _start_server(self):
        self.client.start()

    def step(self, action):
        self._take_action(action)
        ...

    def _take_action(self, action):
        ...

    def _get_reward(self):
        if self.client.opponent_fainted_last_turn:
            return 1
        else:
            return 0

    def reset(self):
        ...

    def render(self, mode='human'):
        ...

    def close(self):
        ...
