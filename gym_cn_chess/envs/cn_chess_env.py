import numpy as np
import pygame
from typing import Any, Tuple, Union, Optional
import re
import copy
import gymnasium as gym
from gymnasium import spaces
from .cn_chess_logic import Position, initial, A0
from .cn_chess_value import get_move_value
from .cn_chess_pygame import CnChessPygame


class CnChessEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}
    
    def __init__(self, render_mode=None):
        # 这定义了缓存的步数，用于存储最近6步的棋局状态。
        # self.cache_steps = 6
        # 初始化棋局状态
        self.pos = Position(initial)
        # 初始化历史棋局状态
        self.his = [copy.copy(self.pos.board)]
        # 创建一个历史记录列表，初始只包含初始棋盘状态的副本，计数= 1
        self.pos_dict = {self.pos.board: 1}
        
        # 观察空间实际上是一个 6x10x9 的三维数组：
        # 每个位置的得分范围为 -7 到 7
        # 6 是缓存步数，10 是棋盘行数，9 是棋盘列数
        # 1-7 代表红方棋子，-1- -7 代表黑方棋子，0 代表空位
        main_observation_space = spaces.Box(-7, 7, (10, 9))  # board 8x8

        self.observation_space = spaces.Box(
            -7, 7, (91, 10, 9)
        )

        # 棋盘的笛卡尔积 + 投降
        # 在中国象棋中，棋盘是 9 10 的
        # 90 来自于 9x10，代表棋盘上的任意一个位置。
        # 90x90 表示从棋盘上的任意一点移动到另一点的所有可能性。
        self.action_space = spaces.Discrete(90 * 90)
        
        # 当前玩家，0 代表红方，1 代表黑方
        self.current_player = 0
        # 是否投降
        self.resigned = [False, False]
        # 棋盘计数
        # 用于记录棋局状态出现的次数。这是一个重要的功能，主要用于处理中国象棋中的和棋规则
        self.board_count = {}
        
        self.window_size = 512  # The size of the PyGame window
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        self.window = None
        self.clock = None
    
    # 生成观察空间
    def generate_observation(self) -> np.ndarray:
        # observation = np.zeros([self.cache_steps, 10, 9])
        # for i, one_pos in enumerate(self.his[::-1][:self.cache_steps]):
        #     # 如果 i 是偶数，则将当前位置的棋盘状态转换为 numpy 数组并存储在 observation 中
        #     if i % 2 == 0:
        #         observation[i] = Position(one_pos).to_numpy()
        #     else:
        #         # 如果 i 是奇数，则将当前位置的棋盘状态旋转 180 度后转换为 numpy 数组并存储在 observation 中
        #         observation[i] = Position(one_pos).rotate().to_numpy()

        # to float 32
        observation = self.pos.to_numpy().astype(np.int8)
        possible_actions = self.get_possible_actions()
        
        # 创建一个全 0 的数组，用于表示所有可能的行动
        action_mask_flatten = np.zeros((90 * 90), dtype=np.int8)
        
        # 根据 possible_actions 更新 action_mask
        for action in possible_actions:
            action_mask_flatten[action] = 1
            
        # action_mask reshape
        action_mask = action_mask_flatten.reshape((90, 10, 9))

        # observation 翻转
        observation = observation[::-1]
        # observation （10， 9） 与 action_mask (90, 10, 9) 合并
        concat_observation = np.concatenate([np.expand_dims(observation, axis=0), action_mask], axis=0)
        
        # 将 concat_observation 第二维度 倒序排列
        # concat_observation = concat_observation[:, ::-1, :]
        return concat_observation
    
    def generate_info(self, value_diff: int = 0) -> dict:
        result = {
            "history": self.get_history_positions(),
            "value": value_diff,
            "is_red_player": self.current_player == 0,
            "is_black_player": self.current_player == 1,
        }

        return result

    def reset(self, *,
              seed: int | None = None,
              options: dict[str, Any] | None = None) -> Tuple[np.ndarray, dict]:
        # > Tuple[ObsType, dict[str, Any]
        
        self.pos = Position(initial)
        self.his = [copy.copy(self.pos.board)]
        self.pos_dict = {self.pos.board: 1}
        self.current_player = 0
        self.resigned = [False, False]
        self.board_count = {}
        
        info = self.generate_info()
        if self.render_mode == "human":
            self._render_frame()
        
        return self.generate_observation(), info
    
    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        """
        执行一步棋
        """
        # 获取可能的行动
        possible_actions = self.get_possible_actions()
        # 断言 action 在 possible_actions 中
        assert (action in possible_actions)
        # 断言当前玩家有将军
        assert (self.pos.player_has_king())
        # 将 action 转换为移动字符串
        action_str = self.action2move(action)
        # 如果 action 是 resign, 投降
        if action_str == "resign":
            assert self.resigned[self.current_player] is not True
            self.resigned[self.current_player] = True
            reward = -1
            terminated = True
            info = self.generate_info()
            truncated = False
            return self.generate_observation(), reward, terminated, truncated, info
        else:
            # action str 应该类似b2e2
            if len(action_str) > 4:
                raise RuntimeError(f"action {action} not recognized")
            # 将动作字符串拆分为起始位置和目标位置
            from_str, to_str = action_str[:2], action_str[2:]
            # 将字符串坐标转换为数字坐标
            from_cord, to_cord = self.str2cord(from_str), self.str2cord(to_str)
            
            # 计算移动带来的价值变化
            value_diff = get_move_value(self.pos.board, (from_cord, to_cord))
            
            # 获取要移动的棋子
            move_piece = self.pos.board[from_cord]
            
            # 执行移动
            self.pos = self.pos.move((from_cord, to_cord))
            
            # 记录历史局面
            self.his.append(copy.copy(self.pos.board))
            self.his = self.his[-6:]  # 只保留最近6个局面
            
            # 更新局面计数
            self.board_count.setdefault(self.pos.board, 0)
            self.board_count[self.pos.board] += 1
            
            reward = 0
            if self.board_count[self.pos.board] >= 3:
                # 如果棋盘状态重复了3次，且移动的棋子不是帅/将，则游戏结束
                if move_piece != "K":
                    terminated = True
                    reward = -1
                else:
                    terminated = False
            elif not self.pos.player_has_king():
                # 这里条件是player has king，但是由于在pos.move中局面被rotate过（红黑交换），所以这里其实在判断这一步完成后是否已经吃掉对方将军
                terminated = True
                reward = 1
            else:
                terminated = False
            # 交换红黑方
            self.current_player = 1 - self.current_player
            
            info = self.generate_info(value_diff)
            
            if self.render_mode == "human":
                self._render_frame()
            
            truncated = False
            
            return self.generate_observation(), reward, terminated, truncated, info
    
    def render(self):
        if self.render_mode == "rgb_array":
            return self._render_frame()
    
    def _render_frame(self):
        if self.render_mode == "human":
            if self.window is None:
                game_window = CnChessPygame(self.pos.board)
                self.window = game_window
                game_window.start()
            else:
                self.clock = pygame.time.Clock().tick(30)
                self.window.update_board_pieces(self.pos.board)
                self.window.update_board()
    
    def get_history_positions(self):
        return [Position(i) for i in self.his]
    
    """
    ==============================
    classmethod
    ==============================
    """
    
    @classmethod
    def str2cord(cls, c):
        fil, rank = ord(c[0]) - ord('a'), int(c[1])
        return A0 + fil - 16 * rank
    
    @classmethod
    def str2action(cls, c):
        fil, rank = ord(c[0]) - ord('a'), int(c[1])
        return fil + 9 * rank
    
    @classmethod
    def cord2str(cls, i):
        rank, fil = divmod(i - A0, 16)
        return chr(fil + ord('a')) + str(-rank)
    
    @classmethod
    def action2str(cls, i):
        rank, fil = divmod(i, 9)
        return chr(fil + ord('a')) + str(rank)
    
    @classmethod
    def resign_action(cls):
        return 90 * 90
    
    @classmethod
    def has_resigned(cls, action):
        return action == cls.resign_action()
    
    @classmethod
    def action2move(cls, action):
        """
        Encode move into action
        """
        if action == cls.resign_action():
            return 'resign'
        elif action < 90 * 90:
            # divmod() 函数等价于同时执行除法和取模运算
            # (a // b, a % b)
            from_act, to_act = divmod(action, 90)
            return cls.action2str(from_act) + cls.action2str(to_act)
    
    @classmethod
    def move_to_action(cls, move):
        """
        Encode move into action
        """
        if move == 'resign':
            return cls.resign_action()
        else:
            match = re.match('([a-i][0-9])' * 2, move)
            if not match:
                raise RuntimeError(f"{match} not recognized")
            from_act, to_act = cls.str2action(match.group(1)), cls.str2action(match.group(2))
            move_int = from_act * 90 + to_act
            return move_int
    
    def get_possible_actions(self):
        moves = self.get_possible_moves()
        return [self.move_to_action(m) for m in moves]
    
    def get_possible_moves(self) -> list[str]:
        """
        获取当前玩家可能的移动
        str: <from_cord><to_cord>
        """
        if self.current_player == 0 or self.current_player == 1:
            # 红方情况
            moves = []
            for from_cord, to_cord in self.pos.gen_moves():
                one_move = self.cord2str(from_cord) + self.cord2str(to_cord)
                moves.append(one_move)
        else:
            raise RuntimeError(f"player {self.current_player} not recognized")
        
        if not self.pos.player_has_king():
            # 如果将军已经被吃掉，那么输了，同样返回空的move数组
            moves = []
        elif self.resigned[self.current_player]:
            # 如果已经投降或者议和，返回空的move数组
            moves = []
        else:
            pass
            # moves.append("resign")
        return moves
