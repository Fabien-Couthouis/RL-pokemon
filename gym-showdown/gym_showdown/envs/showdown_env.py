import gym
import webbrowser
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
        self.action_space = spaces.Discrete(9)
        self.viewer = False
  
    def _start_server(self):
        self.client.start()

    def step(self, action):
        self._take_action(action)
        ob = self.client.get_env_state()
        reward = self._get_reward()
        episode_over = self.client.status != IN_GAME
        return ob, reward, episode_over, {}

    def _take_action(self, action):
        ...

    def _get_reward(self): #Sensible but simple reward function
        if self.client.opponent_fainted_last_turn:
            return 1
        else:
            return 0

    def reset(self):
        ...
        
    def render(self, mode='human'):
        if self.viewer == False:
            webbrowser.open('https://play.pokemonshowdown.com/')

    def close(self):
        ...
