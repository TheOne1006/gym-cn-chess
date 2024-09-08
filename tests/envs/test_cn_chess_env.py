from unittest.mock import MagicMock
import time
import pytest
import numpy as np
from gym_cn_chess.envs import CnChessEnv


class TestCnChessEnv:
    @pytest.fixture
    def env(self):
        """初始化环境实例"""
        return CnChessEnv()
    
    def test_generate_observation(self, env):
        """测试生成观察空间的方法"""
        observation = env.generate_observation()
        assert observation.shape == (91, 10, 9)
        assert (observation >= -7).all()
        assert (observation <= 7).all()
    
    def test_step(self, env):
        """测试 step 方法的行为"""
        # 假设 action 对应一个有效的移动
        actions = env.get_possible_actions()
        # 执行 step 并检查返回值类型
        observation, reward, terminated, truncated, info = env.step(actions[0])
        assert isinstance(observation, dict)
        assert isinstance(reward, int)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)
    
    def test_reset(self, env):
        """测试 reset 方法的行为"""
        observation, info = env.reset()
        assert isinstance(observation, dict)
        assert isinstance(info, dict)
    
    def test_render(self, env, monkeypatch):
        """测试渲染方法的行为"""
        env.render_mode = "human"
        
        env.render()
        time.sleep(1)
        
        for _ in range(10):
            actions = env.get_possible_actions()
            # 执行 step 并检查返回值类型
            env.step(actions[0])
            time.sleep(1)
        
        assert env.window is not None
        
    def test_tearDown(self, env):
        """测试环境清理"""
        if env.window is not None:
            env.window = None
            assert env.window is None
