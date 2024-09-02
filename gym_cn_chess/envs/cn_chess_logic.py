from collections import namedtuple
from itertools import count
from typing import Generator, Tuple
import numpy as np

# P: 兵/卒, N: 马/馬, B: 相/象, R: 车/車, A: 士/仕, C: 炮, K: 帅/将

initial = (
    '               \n'  # 0 -  9
    '               \n'  # 10 - 19 
    '               \n'  # 10 - 19
    '   rnbakabnr   \n'  # 20 - 29
    '   .........   \n'  # 40 - 49
    '   .c.....c.   \n'  # 40 - 49
    '   p.p.p.p.p   \n'  # 30 - 39
    '   .........   \n'  # 50 - 59
    '   .........   \n'  # 70 - 79
    '   P.P.P.P.P   \n'  # 80 - 89
    '   .C.....C.   \n'  # 70 - 79
    '   .........   \n'  # 70 - 79
    '   RNBAKABNR   \n'  # 90 - 99
    '               \n'  # 100 -109
    '               \n'  # 100 -109
    '               \n'  # 110 -119
)


pos_str_mapping = {'R': '车', 'N': '马', 'B': '相', 'A': '仕', 'K': '帅', 'P': '兵', 'C': '炮',
                      'r': '俥', 'n': '傌', 'b': '象', 'a': '士', 'k': '将', 'p': '卒', 'c': '砲', '.': '．'}

A0, I0, A9, I9 = 12 * 16 + 3, 12 * 16 + 11, 3 * 16 + 3, 3 * 16 + 11


# N, E, S, W 分别代表北、东、南、西四个方向的移动 (上下左右)
N, E, S, W = -16, 1, 16, -1

# 移动规则之字典
directions = {
    'P': (N, W, E), # 兵/卒 能向 上、左、右 移动
    'N': (N + N + E, E + N + E, E + S + E, S + S + E, S + S + W, W + S + W, W + N + W, N + N + W), # 马/馬
    'B': (2 * N + 2 * E, 2 * S + 2 * E, 2 * S + 2 * W, 2 * N + 2 * W), # 相/象
    'R': (N, E, S, W), # 车/車
    'C': (N, E, S, W), # 炮/砲
    'A': (N + E, S + E, S + W, N + W), # 士/仕
    'K': (N, E, S, W)
}


class Position(namedtuple('Position', 'board')):
    board: str
    """ 游戏状态，使用 256 个字符表示棋盘，每个字符表示棋盘上的一个位置，空格表示空位，其他字符表示棋子
    """

    def gen_moves(self) -> Generator[Tuple[int, int], None, None]:
        """
        生成所有可能的移动
        """
        for i, p in enumerate(self.board):
            if p == 'K':
                # 遍历“帅、将”的移动范围
                for scanpos in range(i - 16, A9, -16):
                    if self.board[scanpos] == 'k':
                        yield (i, scanpos)
                    elif self.board[scanpos] != '.':
                        break
            if not p.isupper(): continue
            # 炮/砲 的移动范围
            if p == 'C':
                # 根据字典的定义，炮/砲 的移动范围是四个方向  d = N, E, S, W
                for d in directions[p]:
                    # cfoot 炮的 垫脚
                    cfoot = 0
                    # from itertools import count
                    # count(start, step)， 创建一个无限的迭代器, start：序列的起始值，step：步长
                    # 从 i + d 开始，每次增加 d
                    # i 是当前炮的位置，d 是移动的方向（上下左右之一）
                    # 这样可以沿着一个方向不断移动，直到遇到边界或其他条件停止
                    for j in count(i + d, d):
                        q = self.board[j]   # q = 目标位置的字符
                        if q.isspace(): break # 遇到边界, string 对象方法
                        if cfoot == 0 and q == '.': # 垫脚为空，且位置为空，可位移
                            yield (i, j)
                        elif cfoot == 0 and q != '.': # 垫脚不为空，且位置存在棋子，垫脚数+1，不可位移，位置跳过
                            cfoot += 1
                        elif cfoot == 1 and q.islower(): # 垫脚数为1，且目标位置为敌方棋子，可位移
                            yield (i, j)
                            break
                        elif cfoot == 1 and q.isupper():
                            break
                continue
            # 其他棋子的移动范围
            # 其他棋子包括 士、相、马、兵、车
            for d in directions[p]:
                # 读取 字典 directions 中 棋子 p 的移动规则
                for j in count(i + d, d):
                    q = self.board[j] # q = 目标位置的字符
                    # 超出范围，或者是 己方棋子
                    if q.isspace() or q.isupper(): break
                    # 过河的卒/兵才能横着走
                    if p == 'P' and d in (E, W) and i > 128:
                        break
                    # 士/帅 的移动范围
                    # j & 15 等价于 j % 16但是更快
                    # j < 160 超出田字的前线
                    # j & 15 > 8 超出田字的右线
                    # j & 15 < 6 超出田字的左线
                    elif p in ('A', 'K') and (j < 160 or j & 15 > 8 or j & 15 < 6):
                        break
                    # 相/象 的移动范围，不能过河
                    elif p == 'B' and j < 128:
                        break
                    # 马/馬 的移动范围
                    elif p == 'N':
                        n_diff_x = (j - i) & 15
                        if n_diff_x == 14 or n_diff_x == 2:
                             # 左右跳 蹩马脚
                            if self.board[i + (1 if n_diff_x == 2 else -1)] != '.': break
                        else:
                            # 前后跳 蹩马脚
                            if j > i and self.board[i + 16] != '.':
                                break
                            elif j < i and self.board[i - 16] != '.':
                                break
                    # 相/象 田字中间 不能有棋子
                    elif p == 'B' and self.board[i + d // 2] != '.':
                        break
                    # Move it
                    yield (i, j)
                    # Stop crawlers from sliding, and sliding after captures
                    if p in 'PNBAK' or q.islower(): break

    def rotate(self):
        ''' 方法旋转棋盘,用于切换红黑方 '''
        # +" " 避免开头始终为 空格
        return Position(
            self.board[-2::-1].swapcase() + " ")

    @staticmethod
    def rotate_board_str(board_str):
        return board_str[-2::-1].swapcase() + " "

    def move(self, move):
        """
        执行棋子移动并返回新的棋局位置。

        函数流程:
        1. 获取 起始和目标位置 信息
        2. 定义一个辅助函数put用于在棋盘上放置棋子
        3. 复制当前棋盘状态
        4. 执行实际的移动:
           - 将起始位置的棋子放到目标位置
           - 将起始位置设为空格

        5. 切换对手

        返回:
        新的Position对象,代表移动后的棋局状态
        """
        i, j = move  # 解包移动的起始和目标位置
        p, q = self.board[i], self.board[j]  # 获取起始位置的棋子和目标位置的内容
        put = lambda board, i, p: board[:i] + p + board[i + 1:]  # 定义辅助函数用于在棋盘上放置棋子
        board = self.board  # 当前棋盘状态
        # 执行实际的移动
        board = put(board, j, board[i])  # 将起始位置的棋子放到目标位置
        board = put(board, i, '.')  # 将起始位置设为空格
        return Position(board).rotate()  # 创建新的Position对象并旋转棋盘（切换对手）

    # # todo: 评估函数
    # def value(self, move):
    #     i, j = move
    #     p, q = self.board[i], self.board[j]
    #     # Actual move，移动得分
    #     score = pst[p][j] - pst[p][i]
    #     # Capture，吃掉棋子得分
    #     if q.islower():
    #         score += pst[q.upper()][255 - j - 1]
    #     return score

    # 判断当前玩家是否有帅/将
    def player_has_king(self):
        return "K" in self.board

    # 判断对手是否有帅/将，opponent 对手
    def oppo_has_king(self):
        return "k" in self.board

    # 打印位置信息
    def print_pos(self):
        out_str = "\n"
        uni_pieces = {'R': '车', 'N': '马', 'B': '相', 'A': '仕', 'K': '帅', 'P': '兵', 'C': '炮',
                      'r': '俥', 'n': '傌', 'b': '象', 'a': '士', 'k': '将', 'p': '卒', 'c': '砲', '.': '．'}
        for i, row in enumerate(self.board.split()):
            out_str += "{}{}{}\n".format(' ', 9 - i, ''.join(uni_pieces.get(p, p) for p in row))
        out_str += '  ａｂｃｄｅｆｇｈｉ\n\n'
        return out_str

    def to_numpy(self):
        out_str = "\n"
        uni_pieces = {'R': 1, 'N': 2, 'B': 3, 'A': 4, 'K': 5, 'P': 6, 'C': 7,
                      'r': -1, 'n': -2, 'b': -3, 'a': -4, 'k': -5, 'p': -6, 'c': -7, '.': 0}
        ind = 0
        out_array = np.zeros((10, 9))
        for i, row in enumerate(self.board.split()):
            row = row.replace(" ", "")
            if row:
                out_array[ind] = np.asarray([uni_pieces[j] for j in row])
                ind += 1
        return out_array





