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
        self.client = Client(name=username, password=password, team=team)
        self.action_space = spaces.Discrete(10)
        self.viewer = False
        self.action_invalid = False
  
    def _start_server(self):
        self.client.start()
        self.client.search_battles(self.client.team, 'ou')

    def step(self, action):
        self._take_action(action)
        ob = self.client.get_env_state()
        reward = self._get_reward()
        episode_over = self.client.status != IN_GAME
        return ob, reward, episode_over, {}

    def _take_action(self, action):
        if action < 4: #Agent chose to use a move from current poke
            if self.client.check_if_move_valid(action): #TODO
                self.client.move_from_id(action)
            else:
                self.action_invalid = True
        elif action < 10: #Agent chose to switch to another pokemon
            if self.client.check_if_switch_valid(action): #TODO
                self.client.switch_from_id(action-4)
            else:
                self.action_invalid = True
        else:
            print("Unknown action")


    def _get_reward(self): #Sensible but simple reward function
        if self.client.status == WIN:
            return 1
        elif self.action_invalid:
            self.action_invalid = False
            return -1
        else:
            return 0

    def reset(self):
        if self.client.status == IN_GAME:
            self.client.forfeit(self.client.battle)
        self.client.search_battles(self.client.team, 'ou')
        
    def render(self, mode='human'):
        if self.viewer == False:
            webbrowser.open('https://play.pokemonshowdown.com/')

    def close(self):
        self.client.forfeit(self.client.battle)
