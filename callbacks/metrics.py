from typing import Dict

import numpy as np
from ray.rllib.agents.callbacks import DefaultCallbacks
from ray.rllib.env import BaseEnv
from ray.rllib.evaluation import MultiAgentEpisode, RolloutWorker
from ray.rllib.policy import Policy
from ray.rllib.policy.sample_batch import SampleBatch


class MetricsCallbacks(DefaultCallbacks):
    def on_episode_start(self, worker: RolloutWorker, base_env: BaseEnv,
                         policies: Dict[str, Policy],
                         episode: MultiAgentEpisode, **kwargs):
        episode.hist_data["actions"] = []

    def on_episode_step(self, worker: RolloutWorker, base_env: BaseEnv,
                        episode: MultiAgentEpisode, **kwargs):
        info = episode.last_info_for()
        if info:
            # # Ignore first episode step (after .reset()) where info is None or {} (empty dict)
            # step_metrics = info["metrics"]["step"]
            # for metric_name, metric in step_metrics.items():
            #     # Store step metrics
            #     if episode.user_data.get(metric_name, None) is None:
            #         # Create list of metrics if first step
            #         episode.user_data[metric_name] = []
            #     episode.user_data[metric_name].append(metric)

            # Log action in tensorboard histogram
            episode.hist_data["actions"].append(episode.last_action_for())

    def on_episode_end(self, worker: RolloutWorker, base_env: BaseEnv,
                       policies: Dict[str, Policy], episode: MultiAgentEpisode,
                       **kwargs):
        info = episode.last_info_for()
        end_metrics = info["metrics"]["end"]
        for metric_name, metric in end_metrics.items():
            episode.custom_metrics[metric_name] = metric

        # step_metrics = info["metrics"]["step"]
        # for metric_name in step_metrics:
        #     mean_metric = np.mean(episode.user_data[metric_name])
        #     episode.custom_metrics[metric_name] = mean_metric

    def on_sample_end(self, worker: RolloutWorker, samples: SampleBatch,
                      **kwargs):
        pass

    def on_train_result(self, trainer, result: dict, **kwargs):
        pass

    def on_postprocess_trajectory(
            self, worker: RolloutWorker, episode: MultiAgentEpisode,
            agent_id: str, policy_id: str, policies: Dict[str, Policy],
            postprocessed_batch: SampleBatch,
            original_batches: Dict[str, SampleBatch], **kwargs):
        if "num_batches" not in episode.custom_metrics:
            episode.custom_metrics["num_batches"] = 0
        episode.custom_metrics["num_batches"] += 1
