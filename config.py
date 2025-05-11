# config.py
# (YYYY-MM-DD): 2025-05-10 - Configuration values for CTkTetris
# (YYYY-MM-DD): 2025-05-11 - Added SRS-like kick data and reward thresholds

import pygame

# --- Screen and Game Area Dimensions ---
WINDOW_WIDTH = 850  # Increased width slightly for rewards display
WINDOW_HEIGHT = 700

GAME_AREA_FRAME_WIDTH = 300
GAME_AREA_FRAME_HEIGHT = 600

INFO_AREA_WIDTH = 250 # Increased width for rewards display

BLOCK_SIZE = 30

GRID_COLS = GAME_AREA_FRAME_WIDTH // BLOCK_SIZE
GRID_ROWS = GAME_AREA_FRAME_HEIGHT // BLOCK_SIZE

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRID_COLOR = (50, 50, 50)
EMPTY_CELL_COLOR = (30, 30, 30)

TETROMINO_COLORS = {
    'I': (0, 255, 255),   # Cyan
    'O': (255, 255, 0),   # Yellow
    'T': (128, 0, 128),   # Purple
    'S': (0, 255, 0),     # Green
    'Z': (255, 0, 0),     # Red
    'J': (0, 0, 255),     # Blue
    'L': (255, 165, 0)    # Orange
}

# --- Tetromino Shapes ---
# Each shape is a list of (row, col) offsets from a pivot point for each rotation state
# Rotation states: 0 (initial), 1 (R), 2 (2), 3 (L)
TETROMINO_SHAPES = {
    'I': [ # Centered differently for I piece rotations
        [(1, 0), (1, 1), (1, 2), (1, 3)],  # 0 state (flat)
        [(0, 2), (1, 2), (2, 2), (3, 2)],  # 1 state (vertical)
        [(2, 0), (2, 1), (2, 2), (2, 3)],  # 2 state (flat, offset)
        [(0, 1), (1, 1), (2, 1), (3, 1)]   # 3 state (vertical, offset)
    ],
    'O': [
        [(0, 0), (0, 1), (1, 0), (1, 1)] # Only one rotation state
    ],
    'T': [
        [(0, 1), (1, 0), (1, 1), (1, 2)],  # 0
        [(0, 1), (1, 1), (1, 2), (2, 1)],  # 1 (R)
        [(1, 0), (1, 1), (1, 2), (2, 1)],  # 2
        [(0, 1), (1, 0), (1, 1), (2, 1)]   # 3 (L)
    ],
    'S': [
        [(0, 1), (0, 2), (1, 0), (1, 1)],  # 0
        [(0, 1), (1, 1), (1, 2), (2, 2)]   # 1 (R)
    ], # S only has 2 distinct rotation states
    'Z': [
        [(0, 0), (0, 1), (1, 1), (1, 2)],  # 0
        [(0, 2), (1, 1), (1, 2), (2, 1)]   # 1 (R)
    ], # Z only has 2 distinct rotation states
    'J': [
        [(0, 0), (1, 0), (1, 1), (1, 2)],  # 0
        [(0, 1), (0, 2), (1, 1), (2, 1)],  # 1 (R)
        [(1, 0), (1, 1), (1, 2), (2, 2)],  # 2
        [(0, 1), (1, 1), (2, 0), (2, 1)]   # 3 (L)
    ],
    'L': [
        [(0, 2), (1, 0), (1, 1), (1, 2)],  # 0
        [(0, 1), (1, 1), (2, 1), (2, 2)],  # 1 (R)
        [(1, 0), (1, 1), (1, 2), (2, 0)],  # 2
        [(0, 0), (0, 1), (1, 1), (2, 1)]   # 3 (L)
    ]
}
# Note: The pivot for these shapes is generally the top-left of their bounding box in state 0.
# For SRS, the pivot definition and shape coordinates are very specific. This is a simplification.

# --- Wall Kick Data (Simplified SRS-like) ---
# (dx, dy) offsets to try if direct rotation collides.
# Indexed by piece type, then by (from_rotation_state, to_rotation_state)
# States: 0=Initial, 1=Rotated Right, 2=Rotated 180, 3=Rotated Left
# For S and Z, they only alternate between 0 and 1 effectively.
KICK_DATA_JLSTZ = { # For J, L, S, T, Z pieces
    # (0->1) and (1->0) etc.
    (0, 1): [(0,0), (-1,0), (-1,-1), (0,+2), (-1,+2)], # Test order for 0->R
    (1, 0): [(0,0), (+1,0), (+1,+1), (0,-2), (+1,-2)], # Test order for R->0
    (1, 2): [(0,0), (+1,0), (+1,+1), (0,-2), (+1,-2)], # R->2
    (2, 1): [(0,0), (-1,0), (-1,-1), (0,+2), (-1,+2)], # 2->R
    (2, 3): [(0,0), (+1,0), (+1,-1), (0,+2), (+1,+2)], # 2->L
    (3, 2): [(0,0), (-1,0), (-1,+1), (0,-2), (-1,-2)], # L->2
    (3, 0): [(0,0), (-1,0), (-1,-1), (0,+2), (-1,-2)], # L->0
    (0, 3): [(0,0), (+1,0), (+1,+1), (0,-2), (+1,-2)], # 0->L (anticlockwise from 0)
}
KICK_DATA_I = { # I piece has different, often larger, kicks
    (0, 1): [(0,0), (-2,0), (+1,0), (-2,+1), (+1,-2)], # 0->R
    (1, 0): [(0,0), (+2,0), (-1,0), (+2,-1), (-1,+2)], # R->0
    (1, 2): [(0,0), (-1,0), (+2,0), (-1,-2), (+2,+1)], # R->2
    (2, 1): [(0,0), (+1,0), (-2,0), (+1,+2), (-2,-1)], # 2->R
    (2, 3): [(0,0), (+2,0), (-1,0), (+2,-1), (-1,+2)], # 2->L
    (3, 2): [(0,0), (-2,0), (+1,0), (-2,+1), (+1,-2)], # L->2
    (3, 0): [(0,0), (+1,0), (-2,0), (+1,+2), (-2,-1)], # L->0
    (0, 3): [(0,0), (-1,0), (+2,0), (-1,-2), (+2,+1)], # 0->L
}
# O piece does not rotate, so no kick data needed.

# --- Game Speed & Levels ---
INITIAL_FALL_DELAY = 700  # Milliseconds
LEVEL_UP_LINES = 10
SPEED_MULTIPLIER_PER_LEVEL = 0.88
MIN_FALL_DELAY = 80

# --- Scoring ---
SCORE_PER_LINE = [0, 100, 300, 500, 800] # 0, 1, 2, 3, 4 (Tetris) lines
SCORE_SOFT_DROP_PER_ROW = 1
SCORE_HARD_DROP_PER_ROW = 2

# --- Pygame Surface for CTk integration ---
PYGAME_SURFACE_WIDTH = GRID_COLS * BLOCK_SIZE
PYGAME_SURFACE_HEIGHT = GRID_ROWS * BLOCK_SIZE

# --- Rewards ---
REWARD_THRESHOLDS = {
    500: "Great Start! (500 pts)",
    1500: "Awesome! (1500 pts)",
    3000: "Pro Gamer! (3000 pts)",
    5000: "Tetris Master! (5000 pts)",
    10: "Level 10 Reached!" # This will be a level-based reward
}
LEVEL_REWARD_TRIGGER = 10
