# -*- coding: utf-8 -*-
import logging
from client import Client

if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        with open('data/login.txt', 'rt') as f,\
                open('data/mega_charizard.txt', 'rt') as team:
            team = team.read()
            username, password = f.read().strip().splitlines()

        client = Client(name=username, password=password,
                        team=team, search_battle_on_login=False)
        client.start()

    except KeyboardInterrupt:
        raise
