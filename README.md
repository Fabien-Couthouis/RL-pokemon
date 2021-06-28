# RL-pokemon

Bot for pokemon showdown using reinforcement learning (in progress)

## Installation

Install `poke-rl` Anaconda environment:

```bash
conda env create -f environment.yml

```

Install this module:
```bash
pip install e .
```

## Launch local showdown client

Install [NodeJS](https://nodejs.org/en/) if it is not installed on your machine.
```bash

cd pokemon-showdown
node pokemon-showdown start --no-security
```


## Launch training

Launch a training with config specified in [config.yaml](config/config.yaml) config file:
```bash
conda activate poke-rl
python train.py
```