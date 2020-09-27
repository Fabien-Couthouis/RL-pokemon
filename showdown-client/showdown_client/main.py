# -*- coding: utf-8 -*-
# File debug only
import logging
from .client import Client

if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        with open('data/login.txt', 'rt') as f,\
                open('data/team.txt', 'rt') as team,\
        open('data/moves.json') as movedex_file:
            team = team.read()
            username, password = f.read().strip().splitlines()
            movedex_string = movedex_file.read()

        client = Client(name=username, password=password,
                        team=team, movedex_string=movedex_string, search_battle_on_login=False)
        client.start()

    except KeyboardInterrupt:
        raise
