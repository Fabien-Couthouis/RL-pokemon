import gym
import logging
import webbrowser
import threading
from gym import error, spaces, utils
from gym.utils import seeding

try:
    from showdown_client.client import *
except ImportError as e:
    raise error.DependencyNotInstalled(
        f"{e} \n Error: missing dependency showdown_client")


class ClientThread(threading.Thread):

    def __init__(self):
        super().__init__()
        with open('data/login.txt', 'rt') as f,\
                    open('data/team.txt', 'rt') as team:
                team = team.read()
                username, password = f.read().strip().splitlines()
        self.client = Client(name=username, password=password, team=team, search_battle_on_login=True, auto_random=False)
    
    def run(self):
        self.client.start()
        
class ShowdownEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    logging.basicConfig(level=logging.ERROR)
    def __init__(self):
        self.client_thread = ClientThread()
        self.action_space = spaces.Discrete(10)
        self.viewer = False
        self.action_invalid = False
        self._start_server()

    def _start_server(self):
        self.client_thread.start()

    async def step(self, action):
        await self._take_action(action)
        ob = self.client_thread.client.get_env_state()
        reward = self._get_reward()
        episode_over = self.client_thread.client.status != IN_GAME
        if reward != -1:
            self.client_thread.client.wait_for_next_turn()
        return ob, reward, episode_over, {}

    async def _take_action(self, action):
        if action < 4:  # Agent chose to use a move from current poke
            if self.client_thread.client.check_if_move_valid(action):
                await self.client_thread.client.move_from_id(action)
            else:
                self.action_invalid = True
        elif action < 10:  # Agent chose to switch to another pokemon
            if self.client_thread.client.check_if_switch_valid(action):
                await self.client_thread.client.switch_from_id(action-4)
            else:
                self.action_invalid = True
        else:
            print("Unknown action")

    def _get_reward(self):  # Sensible but simple reward function
        if self.client_thread.client.status == WIN:
            return 1
        elif self.action_invalid:
            self.action_invalid = False
            return -1
        else:
            return 0

    def reset(self):
        if self.client_thread.client.status == IN_GAME:
            self.client_thread.client.forfeit(self.client_thread.client.battle)
        self.client_thread.client.search_battles(self.client_thread.client.team, 'ou')
        while self.client_thread.client.status != IN_GAME:
            pass
        return self.client_thread.client.get_env_state()

    def render(self, mode='human'):
        if self.viewer == False:
            webbrowser.open('https://play.pokemonshowdown.com/')

    def close(self):
        if self.client_thread.client.status == IN_GAME:
            self.client_thread.client.forfeit(self.client_thread.client.battle)
        self.client_thread._stop()
