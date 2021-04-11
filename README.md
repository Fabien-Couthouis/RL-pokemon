# RL-pokemon

Bot for pokemon showdown using reinforcement learning (in progress)

## Installation

```bash
pip3 install -e showdown-client
pip3 install -e gym-showdown
```

## Launch local showdown client
```bash
cd pokemon-showdown
node pokemon-showdown start --no-security
```


## Launch training
Launch a training with config specified in [config.yaml](config/config.yaml) config file:
```bash
python train.py
```