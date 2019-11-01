# -*- coding: utf-8 -*-
import showdown
import asyncio
import json
from math import inf
from pprint import pprint  # debug
from brain import Brain, Pokemon


SWITCHING_MOVES = ["U-turn", "Volt Switch"]

IN_GAME = 0
IDLE = 1


class Client(showdown.Client):

    def __init__(self, name, password, team, movedex_string=None, search_battle_on_login=False):
        super().__init__(name, password)
        if movedex_string == None:
            try:
                with open('data/moves.json') as movedex_file:
                    movedex_string = movedex_file.read()
        self.brain = Brain(
            player_name=name, movedex=json.loads(movedex_string))
        self.player = ""
        self.team = team
        self.search_battle_on_login = search_battle_on_login
        self.opponent_fainted_last_turn = False
        self.status = IDLE

    def set_player(self):
        """ Set player var to "p1" or "p2" """
        if self.battle.p1 == self.name:
            self.player = "p1"
        else:
            self.player = "p2"

    def is_player(self, player_info):
        return player_info.startswith(self.player)

    async def on_login(self, login_data):
        """ Called when logged on showdown """
        if self.search_battle_on_login:
            await self.search_battles(self.team, 'gen7ou')

    async def on_challenge_update(self, challenge_data):
        """ Called when challenged on showdown """
        incoming = challenge_data.get('challengesFrom', {})
        for user, tier in incoming.items():
            if 'ou' in tier:
                await self.accept_challenge(user, self.team)

    async def on_room_init(self, battle):
        """ Called at the start of the battle """
        if battle.id.startswith('battle-'):
            self.battle = battle
            self.set_player()
            self.status = IN_GAME

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
            self.brain.update_opponent_moves(info_list)

        # Play turn
        elif info_type == "turn":
            action = self.brain.choose_action()
            if action == "switch":
                new_poke = self.brain.choose_on_switch()
                await self.switch(new_poke)
            elif action == "move":
                move, mega, z = self.brain.choose_move()
                await self.move(move, mega, z)

        # Switch on player poke faint
        elif info_type == "faint" and self.is_player(info_list[0]):
            print("FAINT")
            new_poke = self.brain.choose_on_faint()
            await self.switch(new_poke)

        # Switching move choosen by player (U-turn, ...)
        elif info_type == "move" and self.is_player(info_list[0]) and info_list[1] in SWITCHING_MOVES:
            print("Switching move")
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
            self.status == IDLE
            self.brain.set_game_result(
                "win" if info_list[0] == self.name else "lost")

    async def lead_with(self, pokemon):
        """Pokemon sent while in teampreview"""
        await self.client.use_command(self.battle.id, 'team', '{}'.format(pokemon.team_id), delay=0, lifespan=inf)

    async def move(self, move, mega, z):
        """Play a move"""
        mega_str = " mega" if mega else ''
        z_str = " zmove" if z else ''
        await self.client.use_command(self.battle.id, 'choose', 'move {}{}{}'.format(move, mega_str, z_str), delay=0, lifespan=inf)

    async def switch(self, pokemon):
        """Switch to another pokemon"""
        await self.client.use_command(self.battle.id, 'choose', 'switch {}'.format(pokemon.team_id), delay=0, lifespan=inf)
