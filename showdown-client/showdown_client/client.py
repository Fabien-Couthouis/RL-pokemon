# -*- coding: utf-8 -*-
import showdown
import asyncio
import json
import time
from math import inf
from pprint import pprint  # debug
from .brain import Brain, Pokemon


SWITCHING_MOVES = ["U-turn", "Volt Switch"]


IN_GAME = 0
LOSS = 1
WIN = 2
IDLE = 3


class Client(showdown.Client):

    def __init__(self, name, password, team, tier='gen8ou', movedex_string=None, server_host=None, search_battle_on_login=False, auto_random=False):
        super().__init__(name, password, server_host=server_host)
        if movedex_string == None:
            try:
                with open('data/moves.json') as movedex_file:
                    movedex_string = movedex_file.read()
            except FileNotFoundError:
                print("Could not find movedex file")
        self.brain = Brain(
            player_name=name, movedex=json.loads(movedex_string))
        self.name = name
        self.player = None
        self.team = team
        self.tier = tier
        self.search_battle_on_login = search_battle_on_login
        self.opponent_fainted_last_turn = False
        self.status = IDLE
        self.auto_random = auto_random
        self.must_take_additional_action = False

    def set_player(self):
        """ Set player var to "p1" or "p2" """
        if self.battle.title.startswith(self.name):
            self.player = "p1"
        else:
            self.player = "p2"

    def is_player(self, player_info):
        return player_info.startswith(self.player)
    
    def serialize_pokemon(poke):
        serial = []
        serial[0] = poke.


    def get_env_state(self):
        return [self.brain.current_turn, self.brain.active_poke, self.brain.player_pokemons, self.brain.opponent_pokemons]

    def wait_for_next_turn(self):
        turn = self.brain.current_turn
        while self.brain.current_turn == turn and self.status == IN_GAME and self.must_take_additional_action == False:
            time.sleep(0.2)

    async def on_login(self, login_data):
        """ Called when logged on showdown """
        if self.search_battle_on_login:
            await self.search_battles(self.team, self.tier)

    async def on_challenge_update(self, challenge_data):
        """ Called when challenged on showdown """
        incoming = challenge_data.get('challengesFrom', {})
        for user, tier in incoming.items():
            if self.tier in tier:
                await self.accept_challenge(user, self.team)

    async def on_room_init(self, battle):
        """ Called at the start of the battle """
        if battle.id.startswith('battle-'):
            self.battle = battle
            self.set_player()

            await asyncio.sleep(2)
            await self.battle.say('Hello :)')

    async def on_receive(self, *info):
        """ Called on info received from showdown client """
        print("Received ", info)
        info_type = info[1]
        info_list = info[2]

        # Got player pokemons info
        if info_type == "request" and info_list != ['']:
            jsoned_info = json.loads(info_list[0])
            self.brain.update_poke_list(jsoned_info)

        # Teampreview
        elif info_type == "teampreview":
            first_pokemon = self.brain.choose_teampreview()
            await self.lead_with(first_pokemon)

        # Got opponent pokemons info
        elif info_type == "poke":
            self.brain.fill_opponent_pokemons(info_list)

        # Update opponent pokemons conditions
        elif info_type == "-damage" and self.is_player(info_list[0]):
            self.brain.update_opponent_conditions(info_list)

        elif info_type == "move" and not self.is_player(info_list[0]):
            print("info_list[0]", info_list[0])
            print("player", self.player)
            print("IsPlayer", self.is_player(info_list[0]))
            self.brain.update_opponent_moves(info_list)

        # Play turn
        elif info_type == "turn":
            self.brain.current_turn += 1
            if self.brain.current_turn <= 1:
                self.status = IN_GAME
            if self.auto_random:
                action = self.brain.choose_action()
                if action == "switch":
                    new_poke = self.brain.choose_on_switch()
                    await self.switch(new_poke)
                elif action == "move":
                    move, mega, z = self.brain.choose_move()
                    await self.move(move, mega, z)

        # Switch on player poke faint
        elif info_type == "faint":  # and self.is_player(info_list[0]):
            print(info_list)
            print("FAINT")
            if self.auto_random:
                new_poke = self.brain.choose_on_faint()
                await self.switch(new_poke)
            self.must_take_additional_action = True

        # Switching move choosen by player (U-turn, ...)
        elif info_type == "move" and self.is_player(info_list[0]) and info_list[1] in SWITCHING_MOVES and self.brain.is_switch_needed():
            print("Switching move")
            print("info_list[0]", info_list[0])
            print("player", self.player)
            print("IsPlayer", self.is_player(info_list[0]))
            self.must_take_additional_action = True
            if self.auto_random:
                new_poke = self.brain.choose_on_switching_move()
                await self.switch(new_poke)

        # Debug (sent "log" in chat)
        elif info_type == "c" and info_list[1] == "log":
            print(self.brain.opponent_pokemons[1])
            for pokemon in self.brain.opponent_pokemons:
                print(pokemon.name)
                print(pokemon.moves)

        # End of game
        elif info_type == 'win':
            a = ""
            if info_list[0] == self.name:
                self.status = WIN
                a = "win"
            else:
                self.status = LOSS
                a = "loss"
            print("a:", a)
            print("status:", self.status)
            self.brain.set_game_result(a)

    async def lead_with(self, pokemon):
        """Pokemon sent while in teampreview"""
        await self.client.use_command(self.battle.id, 'team', '{}'.format(pokemon.team_id), delay=0, lifespan=inf)

    async def move(self, move, mega, z):
        """Play a move"""
        mega_str = " mega" if mega else ''
        z_str = " zmove" if z else ''
        print(f"Chosen move: {move}")
        await self.client.use_command(self.battle.id, 'choose', 'move {}{}{}'.format(move, mega_str, z_str), delay=0, lifespan=inf)

    def check_if_move_valid(self, id):
        if self.must_take_additional_action:
            return False
        return self.brain.check_move_validity(id)

    def check_if_switch_valid(self, id):
        return self.brain.check_switch_validity(id+1)

    async def move_from_id(self, id):
        """Play a move by chosing it from its id"""
        move, mega, z = self.brain.choose_move(random=False, id=id)
        await self.move(move, mega, z)

    async def switch_from_id(self, id):
        """Switch to another pokemon according to its id"""
        self.must_take_additional_action = False
        pokemon = self.brain.get_poke_from_id(id+1)
        await self.switch(pokemon)

    async def switch(self, pokemon):
        """Switch to another pokemon"""
        await self.client.use_command(self.battle.id, 'choose', 'switch {}'.format(pokemon.team_id), delay=0, lifespan=inf)

    def reset(self):
        self.status = IDLE
        self.brain.reset()
