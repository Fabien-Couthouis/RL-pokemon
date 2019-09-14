import random


class Pokemon():
    def __init__(self, team_id, name, moves=[], condition="", ability="", item=None):
        self.team_id = team_id
        self.name = name
        self.moves = moves
        self.condition = condition
        self.ability = ability
        self.item = item
        self.status = None
        self.can_mega = False

        if not self.item or "-Mega" in self.name:  # as first assumption, opponent pokemons can t mega
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
        self.player_pokemons = [None]
        self.opponent_pokemons = [None]
        self._game_result = None  # "win" or "lost" (when game ends)

    def set_game_result(self, result):
        self._game_result = result

    def get_poke_name(self, non_conform_name):
        """ Remove unwanted chars in the pokemon name ("player, genre, ...)"""
        if ": " in non_conform_name:
            return non_conform_name.split(": ", 1)[1]
        elif "," in non_conform_name:
            return non_conform_name.split(",", 1)[0]
        else:
            return non_conform_name

    def get_random_poke(self, exclude_active=False):
        """Get a random pokemon from player pokemons list """
        if exclude_active:
            non_active_pokemons = self.player_pokemons.copy()
            non_active_pokemons[self.active_poke.team_id] = None
            selecting_list = list(filter(None, non_active_pokemons))
        else:
            selecting_list = list(filter(None, self.player_pokemons))

        return random.choice(selecting_list)

    def get_opponent_poke_from_name(self, poke_name):
        """Get a pokemon from his name in opponent pokemons list """
        for pokemon in self.opponent_pokemons:
            if pokemon.name == poke_name:
                return pokemon
        return None

    def get_random_move(self, valid_moves):
        """Get a random move in valid_moves """
        return random.choice(valid_moves)

    def update_poke_list(self, info):
        """Update name, items, condition,... in player pokemon list"""

        print("UPDATE")
        self.player_pokemons = [None]
        side = info["side"]
        pokemons = side["pokemon"]

        for team_id, poke_info in enumerate(pokemons, 1):
            pokemon = Pokemon(team_id=team_id,
                              name=self.get_poke_name(poke_info["details"]),
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

    def fill_opponent_pokemons(self, pokemon_list):
        """Fill the list of opponent pokemons on "poke" client info"""

        print("filling opponent list")
        pokemon = Pokemon(team_id=len(self.opponent_pokemons),
                          name=self.get_poke_name(pokemon_list[1]))
        self.opponent_pokemons.append(pokemon)

    def update_opponent_conditions(self,  info_list):
        """Update life of the concerned pokemon on "-damage" client info"""
        poke_name = self.get_poke_name(info_list[0])
        pokemon = self.get_opponent_poke_from_name(poke_name)
        # Faint pokemon
        if info_list[1] == "0 fnt":
            index_in_list = pokemon.team_id
            self.opponent_pokemons[index_in_list] = None
        else:
            pokemon.condition = info_list[1]

    def update_opponent_moves(self,  info_list):
        """Update moves of the concerned pokemon on "move" client info"""
        poke_name = self.get_poke_name(info_list[0])
        pokemon = self.get_opponent_poke_from_name(poke_name)
        move = info_list[1]
        if not move in pokemon.moves:
            pokemon.moves.append(move)

    def choose_move(self):
        """Select a valid move for the active pokemon this turn"""
        # Notes : pokemon will always mega if possible. Random move for now
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
        """Select pokemon for teampreview"""
        lead_pokemon = self.get_random_poke()

        self.active_poke = lead_pokemon
        print(self.active_poke.name, "I'm choosing you !", )
        return lead_pokemon

    def choose_action(self):
        """Select action for this turn (switch or move)"""
        switching_prob = 0.3
        if random.random() < switching_prob:
            action = "switch"
        else:
            action = "move"
        return action

    def choose_on_faint(self):
        """Select action on faint"""
        print("fainted")
        return self.choose_on_switch()

    def choose_on_switch(self):
        """Select action on player switch"""
        pokemon = self.get_random_poke(exclude_active=True)
        return pokemon

    def choose_on_switching_move(self):
        """Select action on player switching move"""
        return self.choose_on_switch()
