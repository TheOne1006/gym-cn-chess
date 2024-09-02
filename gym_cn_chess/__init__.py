from gymnasium.envs.registration import register

register(
    id='gym_cn_chess/CnChess-v0',
    entry_point='gym_cn_chess.envs:CnChessEnv',
)

# register(
#      id="gym_examples/GridWorld-v0",
#      entry_point="gym_examples.envs:GridWorldEnv",
#      max_episode_steps=300,
# )
