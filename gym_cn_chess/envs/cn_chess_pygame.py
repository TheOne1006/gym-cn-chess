# 用于显示棋盘

import pygame
from .cn_chess_logic import Position, initial, pos_str_mapping
import os


class ChessPiece:
    def __init__(self, name, color):
        self.name = name
        if name not in pos_str_mapping:
            print(f"Invalid piece name: {name}")
        self.name_cn = pos_str_mapping[name]
        self.color = color
    
    def __str__(self):
        return self.name if self.color == 'red' else self.name.lower()


class CnChessPygame:
    def __init__(self, board_str='', window_width=500, window_height=600):
        """
        window_size: 窗口大小
        board_str: 棋盘字符串
        """
        self.board: list[list[ChessPiece | None]] = [[None for _ in range(9)] for _ in range(10)]
        self.window_height = window_height
        self.window_width = window_width
        self.board_margin = 50
        self.cell_size = (window_width - 2 * self.board_margin) // 8
        self.board_color = (210, 180, 140)  # 棋盘颜色
        self.line_color = (0, 0, 0)  # 线条颜色
        
        pygame.init()
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("中国象棋")
        
        # 加载字体
        font_path = os.path.join(os.path.dirname(__file__), 'SimHei.ttf')
        self.font = pygame.font.Font(font_path, 30)
        
        # 创建两个图层
        self.background_layer = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        self.pieces_layer = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        
        self.board_str = self.format_board_str(board_str)
    
    def update_board_pieces(self, new_board_str):
        """
        更新棋盘棋子信息
        """
        
        format_board_str = self.format_board_str(new_board_str)
        for i, row in enumerate(format_board_str.split('\n')):
            for j, piece in enumerate(row):
                ori_piece = self.board[i][j]
                # 如果棋子位置不变，则不更新
                if ori_piece is not None and ori_piece.name == piece:
                    continue
                
                # 判断  piece 为空
                if piece == '.' or piece.strip() == '':
                    self.board[i][j] = None
                    continue
                
                # 执行更新
                if piece.isupper():
                    color = 'red'
                else:
                    color = 'black'
                
                self.board[i][j] = ChessPiece(piece, color)
    
    def init_board(self):
        """
        初始化棋盘
        """
        for i, row in enumerate(self.board_str.split('\n')):
            for j, piece in enumerate(row):
                if piece == '.':
                    self.board[i][j] = None
                    continue
                
                if piece.isupper():
                    color = 'red'
                else:
                    color = 'black'
                self.board[i][j] = ChessPiece(piece, color)
    
    def init_background_layer(self):
        """
        绘制棋盘图层
        """
        # 填充背景色
        self.background_layer.fill(self.board_color)
        
        # 绘制横线
        for i in range(10):
            y = self.board_margin + i * self.cell_size
            
            pygame.draw.line(self.background_layer, self.line_color,
                             (self.board_margin, y),
                             (self.window_width - self.board_margin, y), 2)
        
        # 绘制竖线
        for i in range(9):
            x = self.board_margin + i * self.cell_size
            if i == 0 or i == 8:
                pygame.draw.line(self.background_layer, self.line_color,
                                 (x, self.board_margin),
                                 (x, self.window_height - self.board_margin * 2), 2)
            else:
                pygame.draw.line(self.background_layer, self.line_color,
                                 (x, self.board_margin),
                                 (x, self.board_margin + 4 * self.cell_size), 2)
                pygame.draw.line(self.background_layer, self.line_color,
                                 (x, self.board_margin + 5 * self.cell_size),
                                 (x, self.window_height - self.board_margin * 2), 2)
        # 绘制"楚河汉界"
        river_y = self.board_margin + 4.5 * self.cell_size
        text = self.font.render("楚 河    汉 界", True, self.line_color)
        text_rect = text.get_rect(center=(self.window_width // 2, river_y))
        self.background_layer.blit(text, text_rect)
        
        # 在draw_board方法中替换原有的斜线绘制代码
        # 绘制斜线（九宫格）
        top_left = self.board_margin + 3 * self.cell_size
        top_right = self.board_margin + 5 * self.cell_size
        bottom = self.window_height - self.board_margin * 2
        
        # 上方九宫
        self._draw_diagonal(top_left, self.board_margin, top_right, self.board_margin + 2 * self.cell_size)
        self._draw_diagonal(top_right, self.board_margin, top_left, self.board_margin + 2 * self.cell_size)
        
        # 下方九宫
        self._draw_diagonal(top_left, bottom, top_right, bottom - 2 * self.cell_size)
        self._draw_diagonal(top_right, bottom, top_left, bottom - 2 * self.cell_size)
        # 更新显示
        # pygame.display.flip()
        
        # 将棋盘图层绘制到屏幕上
        self.screen.blit(self.background_layer, (0, 0))
    
    def _draw_diagonal(self, start_x, start_y, end_x, end_y):
        """
        绘制斜线
        """
        pygame.draw.line(self.background_layer, self.line_color,
                         (start_x, start_y),
                         (end_x, end_y), 2)
    
    def draw_piece(self, piece, row, col):
        """
        在棋子图层上绘制棋子
        """
        # 计算棋子的中心位置
        center_x = self.board_margin + col * self.cell_size
        center_y = self.board_margin + row * self.cell_size
        
        # 绘制棋子背景（圆形）
        radius = self.cell_size // 2 - 2
        if piece.color == 'red':
            bg_color = (255, 0, 0)  # 红色
        else:
            bg_color = (0, 0, 0)  # 黑色
        pygame.draw.circle(self.pieces_layer, bg_color, (center_x, center_y), radius)
        
        # 绘制棋子边框
        pygame.draw.circle(self.pieces_layer, (255, 215, 0), (center_x, center_y), radius, 2)
        
        # 绘制棋子文字
        text_color = (255, 255, 255) if piece.color == 'black' else (255, 255, 0)
        text = self.font.render(piece.name_cn, True, text_color)
        text_rect = text.get_rect(center=(center_x, center_y))
        self.pieces_layer.blit(text, text_rect)
    
    def render(self):
        """
        渲染所有图层到屏幕
        """
        self.screen.blit(self.background_layer, (0, 0))
        self.screen.blit(self.pieces_layer, (0, 0))
        pygame.display.update()
    
    def update_board(self):
        """
        更新棋盘
        """
        self.draw_pieces()
        self.render()
    
    def draw_pieces(self):
        """
        更新棋子
        """
        self.pieces_layer.fill((0, 0, 0, 0))  # 清空棋子图层
        
        for i, row in enumerate(self.board):
            for j, piece in enumerate(row):
                if piece is not None:
                    self.draw_piece(piece, i, j)
    
    def start(self):
        self.init_board()
        self.init_background_layer()
        self.draw_pieces()
        self.render()
    
    @classmethod
    def close(cls):
        pygame.quit()
    
    @classmethod
    def format_board_str(cls, board_str: str):
        out_array: list[str] = []
        for row in board_str.split():
            row = row.replace(" ", "")
            if row:
                out_array.append(row)
        return "\n".join(out_array)


if __name__ == '__main__':
    import sys
    from time import sleep
    import random
    
    pos = Position(initial)
    
    game = CnChessPygame(pos.board)
    game.start()
    
    step = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        pygame.time.Clock().tick(30)
        
        all_moves = list(pos.gen_moves())
        random_move = random.choice(all_moves)
        
        next_pos = pos.move(random_move)
        sleep(1)
        
        # 是否结束
        if not next_pos.oppo_has_king() or not next_pos.player_has_king():
            break
        
        display_pos = next_pos
        if step % 2 != 0:
            display_pos = next_pos.rotate()
        
        game.update_board_pieces(display_pos.board)
        
        game.update_board()
        
        step += 1
        
        pos = next_pos
