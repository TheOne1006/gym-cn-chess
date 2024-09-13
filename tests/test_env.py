import pytest
import gymnasium as gym
import gym_cn_chess


def test_env():
    env = gym.make("gym_cn_chess/CnChess-v0", render_mode="human")
    env.reset()
    assert type(env.observation_space) == gym.spaces.Dict


test_env()
