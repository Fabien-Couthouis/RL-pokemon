import random


class Pokemon():
    def __init__(self, team_id, name, moves=None, condition=None, ability=None, item=None):
        self.team_id = team_id
        self.name = name
        self.moves = moves
        self.condition = condition
        self.ability = ability
        self.item = item
        self.status = None
        self.can_mega = False

        if "-Mega" in self.name:
            self.can_mega = False
        elif self.item.endswith("ite") or self.item.endswith("itex") or self.item.endswith("itey"):
            self.can_mega = True
        else:
            self.can_mega = False


class Brain():
    def __init__(self, player_name):
        self.player_name = player_name
        self.player = None
        self.battle = None
        self.active_poke = None
        self.current_turn = 0
        self.player_pokemons = []
        self.opponent_pokemons = []
        self._game_result = None  # "win" or "lost" when game ends

    def set_game_result(self, result):
        self._game_result = result

    def get_poke_name(self, name_and_genre):
        return name_and_genre.split(",", 1)[0]

    def get_random_poke(self, exclude_active=False):
        if exclude_active:
            non_active_pokemons = self.player_pokemons.copy()
            non_active_pokemons[self.active_poke.team_id] = None
            selecting_list = list(filter(None, non_active_pokemons))
        else:
            selecting_list = list(filter(None, self.player_pokemons))

        return random.choice(selecting_list)

    def get_random_move(self, valid_moves):
        return random.choice(valid_moves)

    def update_poke_list(self, info):
        print("UPDATE")
        self.player_pokemons = [None]
        side = info["side"]
        pokemons = side["pokemon"]

        for team_id, poke_info in enumerate(pokemons, 1):
            pokemon = Pokemon(team_id=team_id,
                              name=self.get_poke_name(
                                  poke_info["details"]),
                              moves=poke_info["moves"],
                              condition=poke_info["condition"],
                              ability=poke_info["baseAbility"],
                              item=poke_info["item"])

            # Active poke
            if team_id == 1 and "active" in info:
                active_moves = info["active"][0]["moves"]
                pokemon.moves = active_moves
                self.active_poke = pokemon

            # Fainted pokemon
            elif pokemon.condition == "0 fnt":
                pokemon = None

            self.player_pokemons.append(pokemon)

    def fill_opponent_poke_list(self, pokemon_list):
        # pokemon = Pokemon(team_id=len(self.opponent_pokemons)+1,
        #                   name=self.get_poke_name(pokemon_list[1]))
        # self.opponent_pokemons.append(pokemon)
        pass

    def choose_move(self):
        self.current_turn += 1
        # Select a non disabled move
        print("CHOOSE MOVE IN", self.active_poke.moves)
        if "disabled" in self.active_poke.moves[0]:
            valid_moves = []
            for move in self.active_poke.moves:
                if move["disabled"] == False:
                    valid_moves.append(move["id"])
        else:
            valid_moves = self.active_poke.moves

        move = self.get_random_move(valid_moves)
        # Mega only if not already mega
        mega = self.active_poke.can_mega
        if mega:
            self.active_poke.can_mega = False

        return move, mega

    def choose_teampreview(self):
        lead_pokemon = self.get_random_poke()
        # lead_pokemon = self.player_pokemons[4]

        self.active_poke = lead_pokemon
        print(self.active_poke.name, "I'm choosing you !", )
        return lead_pokemon

    def choose_action(self):
        if random.random() < 0.3:
            action = "switch"
        else:
            action = "move"
        return action

    def choose_on_faint(self):
        print("fainted")
        return self.choose_on_switch()

    def choose_on_switch(self):
        pokemon = self.get_random_poke(exclude_active=True)
        # self.active_poke = pokemon
        return pokemon

    def choose_on_switching_move(self):
        return self.choose_on_switch()
