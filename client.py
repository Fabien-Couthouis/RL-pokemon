# -*- coding: utf-8 -*-
import math
import showdown
import logging
import asyncio
import json
from pprint import pprint
from brain import Brain, Pokemon


switching_moves = ["U-turn", "Volt Switch"]

logging.basicConfig(level=logging.INFO)
with open('data/login.txt', 'rt') as f,\
        open('data/mega_charizard.txt', 'rt') as team:
    team = team.read()
    username, password = f.read().strip().splitlines()


class Client(showdown.Client):

    def __init__(self, name, password):
        super().__init__(name, password)
        self.brain = Brain(player_name=name)
        self.player = ""

    def set_player(self):
        if self.battle.p1 == self.name:
            self.player = "p1"
        else:
            self.player = "p2"

    async def on_challenge_update(self, challenge_data):
        incoming = challenge_data.get('challengesFrom', {})
        for user, tier in incoming.items():
            if 'ou' in tier:
                await self.accept_challenge(user, team)

    async def on_room_init(self, battle):
        if battle.id.startswith('battle-'):
            self.battle = battle
            self.set_player()

            await asyncio.sleep(2)
            await self.battle.say('Hello :)')

    async def on_receive(self, *info):
        print("Received ", info)
        info_type = info[1]
        info_list = info[2]

        # Get player pokemon info
        if info_type == "request" and info_list != ['']:
            jsoned_info = json.loads(info_list[0])
            self.brain.update_poke_list(jsoned_info)
        elif info_type == "teampreview":
            first_pokemon = self.brain.choose_teampreview()
            await self.lead_with(first_pokemon)

        # Get opponent pokemon info
        elif info_type == "poke":
            self.brain.fill_opponent_poke_list(info_list)

        # Play turn
        elif info_type == "turn":
            action = self.brain.choose_action()
            if action == "switch":
                new_poke = self.brain.choose_on_switch()
                await self.switch(new_poke)
            elif action == "move":
                move, mega = self.brain.choose_move()
                await self.move(move, mega)
        # Player poke faint
        elif info_type == "faint" and info_list[0].startswith(self.player):
            print("FAINT")
            new_poke = self.brain.choose_on_faint()
            await self.switch(new_poke)

        # Switching move choosen by player
        elif info_type == "move" and info_list[0].startswith(self.player) and info_list[1] in switching_moves:
            new_poke = self.brain.choose_on_switching_move()
            await self.switch(new_poke)

        # End of game
        elif info_type == 'win':
            self.brain.set_game_result(
                "win" if info_list[0] == self.name else "lost")

    async def lead_with(self, pokemon):
        await self.client.use_command(self.battle.id, 'team', '{}'.format(pokemon.team_id), delay=0, lifespan=math.inf)

    async def move(self, move, mega):
        await self.client.use_command(self.battle.id, 'choose', 'move {}{}'.format(move, " mega" if mega else ''), delay=0, lifespan=math.inf)

    async def switch(self, pokemon):
        await self.client.use_command(self.battle.id, 'choose', 'switch {}'.format(pokemon.team_id), delay=0, lifespan=math.inf)


Client(name=username, password=password).start()
