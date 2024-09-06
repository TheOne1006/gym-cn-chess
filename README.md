# 中国象棋 gym

- 基于 gymnasium 的象棋环境
- 参考 [chess.py](https://github.com/Farama-Foundation/PettingZoo/blob/master/pettingzoo/classic/chess/chess.py) 实现
- 参考 [gym_chinese_chess](https://github.com/bupticybee/gym_chinese_chess) 实现
- 使用 [gym-xiangqi](https://github.com/tanliyon/gym-xiangqi/tree/main) 作为 GUI 展示

## 安装

```bash
pip install -e .
```


## 使用
```py

import gymnasium as gym
chinese_chess_ env = gym.make('gym_cn_chess/CnChess-v0')
```

