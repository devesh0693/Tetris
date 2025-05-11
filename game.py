# game.py
# (YYYY-MM-DD): 2025-05-10 - Core Tetris game logic
# (YYYY-MM-DD): 2025-05-11 - Implemented SRS-like wall kicks, basic rewards tracking

import pygame
import random
from config import *

class Tetromino:
    def __init__(self, shape_name, position_offset=(GRID_COLS // 2 - 2, 0)): # Adjusted offset for wider pieces
        self.name = shape_name
        self.all_rotations = TETROMINO_SHAPES[shape_name]
        self.color = TETROMINO_COLORS[shape_name]
        self.rotation_index = 0
        # For S and Z, effectively only 2 rotation states (0 and 1)
        self.num_distinct_rotations = len(self.all_rotations) if self.name not in ['S', 'Z'] else 2

        self.current_shape_coords = self.all_rotations[self.rotation_index]
        self.x = position_offset[0]
        self.y = position_offset[1]

    def get_world_coords(self):
        blocks = []
        for r_offset, c_offset in self.current_shape_coords:
            blocks.append((self.y + r_offset, self.x + c_offset))
        return blocks

    def rotate(self, clockwise=True):
        if self.name == 'O': # O piece doesn't rotate
            return

        if clockwise:
            self.rotation_index = (self.rotation_index + 1) % self.num_distinct_rotations
        else: # Counter-clockwise, not fully implemented with kicks yet, but structure is here
            self.rotation_index = (self.rotation_index - 1 + self.num_distinct_rotations) % self.num_distinct_rotations
        
        self.current_shape_coords = self.all_rotations[self.rotation_index]


class TetrisGame:
    def __init__(self):
        self.grid = self.create_grid()
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.lines_cleared_for_level = 0
        self.fall_delay = INITIAL_FALL_DELAY
        self.game_over = False
        self.paused = False

        self.surface = pygame.Surface((PYGAME_SURFACE_WIDTH, PYGAME_SURFACE_HEIGHT))
        
        self.achieved_rewards = set() # To store keys of achieved rewards

    def create_grid(self, filled_value=None):
        return [[filled_value for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    def new_piece(self):
        shape_name = random.choice(list(TETROMINO_SHAPES.keys()))
        # Ensure I piece spawns more centrally if grid is narrow
        offset_x = GRID_COLS // 2 - 2 if shape_name == 'I' else GRID_COLS // 2 - 1
        return Tetromino(shape_name, position_offset=(offset_x, 0))


    def check_collision(self, piece, offset_x=0, offset_y=0, shape_coords_to_check=None):
        """Checks collision for a piece at a given offset, or with specific shape_coords."""
        # If specific shape_coords are provided (e.g. for a rotated shape before committing), use them.
        # Otherwise, use the piece's current shape_coords.
        
        # The piece's (x,y) is its anchor point on the grid.
        # shape_coords_to_check are relative to this anchor.
        
        coords_to_evaluate = shape_coords_to_check if shape_coords_to_check else piece.current_shape_coords

        for r_local, c_local in coords_to_evaluate:
            r_world = piece.y + r_local + offset_y
            c_world = piece.x + c_local + offset_x

            if not (0 <= c_world < GRID_COLS and 0 <= r_world < GRID_ROWS):
                return True  # Collision with boundary
            if self.grid[r_world][c_world] is not None:
                return True  # Collision with existing block
        return False

    def move(self, dx, dy):
        if self.game_over or self.paused:
            return False # Indicate no move happened

        if not self.check_collision(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            if dy > 0:
                self.score += SCORE_SOFT_DROP_PER_ROW
                self.check_and_trigger_rewards() # Check rewards on score change
            return True # Move successful
        elif dy > 0: # Trying to move down but collision detected
            self.lock_piece()
        return False # Move failed or led to lock

    def rotate_piece(self, clockwise=True): # Default to clockwise
        if self.game_over or self.paused or self.current_piece.name == 'O':
            return

        piece = self.current_piece
        original_rotation_index = piece.rotation_index
        original_x, original_y = piece.x, piece.y # Store original position for full revert if needed

        # Tentatively rotate the piece to get the new shape and rotation index
        piece.rotate(clockwise)
        new_rotation_index = piece.rotation_index
        rotated_shape_coords = piece.all_rotations[new_rotation_index] # Get the target shape

        kick_data_table = KICK_DATA_I if piece.name == 'I' else KICK_DATA_JLSTZ
        
        # Determine the key for kick_data_table (e.g., (0,1) for 0->R)
        # For S and Z, they only cycle 0 and 1.
        if piece.name in ['S', 'Z']:
            # S/Z effectively toggle between state 0 and 1 of their defined shapes
            # Their kick data should reflect this (e.g. (0,1) and (1,0) in KICK_DATA_JLSTZ)
             rotation_key = (original_rotation_index % 2, new_rotation_index % 2)
        else:
             rotation_key = (original_rotation_index, new_rotation_index)


        kick_tests = kick_data_table.get(rotation_key, [(0,0)]) # Default to (0,0) if no specific kicks

        for dx_kick, dy_kick in kick_tests:
            # Check collision with the *rotated shape* at the *kicked position*
            if not self.check_collision(piece, dx_kick, dy_kick, shape_coords_to_check=rotated_shape_coords):
                piece.x += dx_kick
                piece.y += dy_kick
                piece.current_shape_coords = rotated_shape_coords # Commit the new shape
                # piece.rotation_index is already updated by piece.rotate()
                return  # Successful rotation with kick

        # If all kicks fail, revert to original state
        piece.x, piece.y = original_x, original_y
        piece.rotation_index = original_rotation_index
        piece.current_shape_coords = piece.all_rotations[original_rotation_index]


    def lock_piece(self):
        for r_abs, c_abs in self.current_piece.get_world_coords():
            if 0 <= r_abs < GRID_ROWS and 0 <= c_abs < GRID_COLS:
                self.grid[r_abs][c_abs] = self.current_piece.color
            elif r_abs < 0 : # Piece locked partially or fully above the visible grid
                self.game_over = True
                return

        lines_cleared_this_turn = self.clear_lines()
        if lines_cleared_this_turn > 0:
            self.update_score_and_level(lines_cleared_this_turn)

        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()

        if self.check_collision(self.current_piece):
            self.game_over = True
        
        self.check_and_trigger_rewards() # Check rewards after piece lock / game over potentially

    def clear_lines(self):
        lines_to_clear = []
        for r_idx, row in enumerate(self.grid):
            if all(cell is not None for cell in row):
                lines_to_clear.append(r_idx)

        if lines_to_clear:
            for r_idx in sorted(lines_to_clear, reverse=True):
                del self.grid[r_idx]
                self.grid.insert(0, [None for _ in range(GRID_COLS)])
        return len(lines_to_clear)

    def update_score_and_level(self, lines_cleared_count):
        self.score += SCORE_PER_LINE[min(lines_cleared_count, len(SCORE_PER_LINE)-1)] * self.level
        self.lines_cleared_total += lines_cleared_count
        self.lines_cleared_for_level += lines_cleared_count

        if self.lines_cleared_for_level >= LEVEL_UP_LINES:
            self.level_up()
        
        self.check_and_trigger_rewards()

    def level_up(self):
        self.level += 1
        self.lines_cleared_for_level = 0 # Reset for next level
        self.fall_delay = max(MIN_FALL_DELAY, int(self.fall_delay * SPEED_MULTIPLIER_PER_LEVEL))
        print(f"Level Up! Level: {self.level}, Fall Delay: {self.fall_delay}")
        self.check_and_trigger_rewards() # Check level-based rewards

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        rows_dropped = 0
        while not self.check_collision(self.current_piece, 0, 1):
            self.current_piece.y += 1
            rows_dropped +=1
        self.score += SCORE_HARD_DROP_PER_ROW * rows_dropped
        self.lock_piece() # lock_piece will also call check_and_trigger_rewards

    def fall(self):
        if self.game_over or self.paused:
            return
        self.move(0, 1) # move will handle locking if collision occurs

    def toggle_pause(self):
        self.paused = not self.paused

    def reset_game(self):
        self.grid = self.create_grid()
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.lines_cleared_for_level = 0
        self.fall_delay = INITIAL_FALL_DELAY
        self.game_over = False
        self.paused = False
        self.achieved_rewards.clear() # Reset rewards

    def check_and_trigger_rewards(self):
        """Checks if any reward thresholds have been met and returns messages."""
        newly_achieved_messages = []
        # Score-based rewards
        for threshold_score, message in REWARD_THRESHOLDS.items():
            if isinstance(threshold_score, int) and self.score >= threshold_score:
                if threshold_score not in self.achieved_rewards:
                    self.achieved_rewards.add(threshold_score)
                    newly_achieved_messages.append(message)
        
        # Level-based rewards (specific check for LEVEL_REWARD_TRIGGER)
        if self.level >= LEVEL_REWARD_TRIGGER:
            level_reward_key = f"level_{LEVEL_REWARD_TRIGGER}" # Unique key for this reward
            if level_reward_key not in self.achieved_rewards:
                 # Find the message associated with LEVEL_REWARD_TRIGGER (assuming it's unique or first one)
                level_message = REWARD_THRESHOLDS.get(LEVEL_REWARD_TRIGGER, f"Level {LEVEL_REWARD_TRIGGER} Reached!")
                self.achieved_rewards.add(level_reward_key)
                newly_achieved_messages.append(level_message)

        return newly_achieved_messages


    def draw(self, surface):
        surface.fill(EMPTY_CELL_COLOR)

        for r in range(GRID_ROWS):
            pygame.draw.line(surface, GRID_COLOR, (0, r * BLOCK_SIZE), (PYGAME_SURFACE_WIDTH, r * BLOCK_SIZE))
        for c in range(GRID_COLS):
            pygame.draw.line(surface, GRID_COLOR, (c * BLOCK_SIZE, 0), (c * BLOCK_SIZE, PYGAME_SURFACE_HEIGHT))

        for r_idx, row in enumerate(self.grid):
            for c_idx, cell_color in enumerate(row):
                if cell_color:
                    pygame.draw.rect(surface, cell_color,
                                     (c_idx * BLOCK_SIZE, r_idx * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(surface, tuple(max(0, comp-50) for comp in cell_color),
                                     (c_idx * BLOCK_SIZE, r_idx * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

        if self.current_piece and not self.game_over:
            for r_abs, c_abs in self.current_piece.get_world_coords():
                 if 0 <= r_abs < GRID_ROWS :
                    pygame.draw.rect(surface, self.current_piece.color,
                                     (c_abs * BLOCK_SIZE, r_abs * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(surface, tuple(max(0, comp-50) for comp in self.current_piece.color),
                                     (c_abs * BLOCK_SIZE, r_abs * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

        if self.paused and not self.game_over: # Only show PAUSED if game is not over
            font = pygame.font.Font(None, 60) # Using Pygame's default font
            text_surf = font.render("PAUSED", True, WHITE)
            # Semi-transparent overlay
            overlay = pygame.Surface((PYGAME_SURFACE_WIDTH, PYGAME_SURFACE_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128)) # Black with 50% alpha
            surface.blit(overlay, (0,0))
            text_rect = text_surf.get_rect(center=(PYGAME_SURFACE_WIDTH / 2, PYGAME_SURFACE_HEIGHT / 2))
            surface.blit(text_surf, text_rect)

        return surface
