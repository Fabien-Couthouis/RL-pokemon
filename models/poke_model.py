from typing import Dict, List, Tuple, Union

from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.models.torch.torch_modelv2 import TorchModelV2
from ray.rllib.utils.annotations import PublicAPI, override
from ray.rllib.utils.framework import try_import_torch
from ray.rllib.utils.typing import ModelConfigDict, TensorType
from torchinfo import summary

torch, nn = try_import_torch()
if torch is not None:
    import torch.nn.functional as F


class PokeModel(TorchModelV2, nn.Module):

    def __init__(self, obs_space, action_space, num_outputs, model_config, name, **custom_model_config):
        TorchModelV2.__init__(self, obs_space, action_space,
                              num_outputs, model_config, name)
        nn.Module.__init__(self)

        if hasattr(obs_space, "original_space"):
            self.original_space = obs_space.original_space
        else:
            self.original_space = obs_space

        DENSE_SIZE = custom_model_config["dense_size"]
        self._l1 = nn.Linear(self.original_space.shape[0], DENSE_SIZE)
        self._l2 = nn.Linear(self._l1.out_features, DENSE_SIZE)
        self._logits = nn.Linear(self._l2.out_features, num_outputs)
        self._value_branch = nn.Linear(self._l2.out_features, 1)

        print(summary(self))

    @override(TorchModelV2)
    def forward(self, input_dict: Dict[str, TensorType], state: List[TensorType], seq_lens: TensorType) -> Tuple[TensorType, List[TensorType]]:
        obs = input_dict["obs"]

        if type(obs) != torch.Tensor:
            print(obs)
            obs = torch.zeros((10,)).float()   

        x = F.relu(self._l1(obs))
        x = F.relu(self._l2(x))

        logits = self._logits(x)
        self._value_out = self._value_branch(x)
        return logits, state

    @override(TorchModelV2)
    def value_function(self) -> TensorType:
        return torch.reshape(self._value_out, [-1])
