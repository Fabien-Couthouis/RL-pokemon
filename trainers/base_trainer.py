from __future__ import absolute_import

import abc

import numpy as np
import six


@six.add_metaclass(abc.ABCMeta)
class BaseTrainer():
    """Abstract base class for showdown trainers."""

    def __init__(self, action_space) -> None:
        self._action_space = action_space

    def act(self, observation: np.ndarray, reward: float, done: bool):
        raise NotImplementedError()

    @property
    def action_space(self):
        return self._action_space
