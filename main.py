# main.py
# (YYYY-MM-DD): 2025-05-10 - Main script to initialize and run the Tetris game
# (YYYY-MM-DD): 2025-05-11 - Integrated rewards display, refined game state transitions

import pygame
import customtkinter as ctk # Not directly used here, but ui.py uses it
from game import TetrisGame
from ui import TetrisUI
from config import *

class GameRunner:
    def __init__(self):
        pygame.init()
        pygame.font.init() # Explicitly initialize font module

        self.game_logic = TetrisGame()
        self.ui = TetrisUI(
            game_instance_provider=lambda: self.game_logic,
            start_game_cb=self.start_game,
            pause_game_cb=self.toggle_pause,
            reset_game_cb=self.reset_game,
            handle_input_cb=self.handle_keypress
        )
        self.ui.fall_timer_id = None # Give UI a reference to cancel timer if needed on close

        self.game_active = False
        self.fall_timer_id = None # For CTk's after method

    def start_game(self):
        if self.ui.game_over_dialog and self.ui.game_over_dialog.winfo_exists():
            self.ui.game_over_dialog.destroy()

        if not self.game_active:
            self.game_logic.reset_game()
            self.game_active = True
            self.game_logic.paused = False
            self.ui.enable_game_controls(game_is_running=True, game_is_paused=False)
            self.ui.rewards_message_var.set("Game On!") # Reset rewards message
            self.schedule_next_fall()
            print("Game started")

    def reset_game(self):
        if self.fall_timer_id:
            self.ui.after_cancel(self.fall_timer_id)
            self.fall_timer_id = None
        
        self.game_logic.reset_game()
        self.game_active = False
        self.ui.enable_game_controls(game_is_running=False)
        self.ui.update_score_display(self.game_logic.score)
        self.ui.update_level_display(self.game_logic.level)
        self.ui.draw_next_piece(self.game_logic.next_piece)
        self.ui.rewards_message_var.set("Game Reset. Start a new game!")
        
        # Draw initial empty board
        empty_surface = pygame.Surface((PYGAME_SURFACE_WIDTH, PYGAME_SURFACE_HEIGHT))
        empty_surface.fill(EMPTY_CELL_COLOR) # Use config color
        self.ui.update_game_canvas(self.game_logic.draw(empty_surface))
        print("Game reset")

    def toggle_pause(self):
        if not self.game_active or self.game_logic.game_over:
            return self.game_logic.paused 

        self.game_logic.toggle_pause()
        if self.game_logic.paused:
            if self.fall_timer_id:
                self.ui.after_cancel(self.fall_timer_id)
                self.fall_timer_id = None
            print("Game paused")
        else:
            self.schedule_next_fall() # Reschedule fall on unpause
            print("Game resumed")
        
        self.ui.enable_game_controls(game_is_running=True, game_is_paused=self.game_logic.paused)
        self.update_ui_elements() # Redraw to show/hide PAUSED overlay
        return self.game_logic.paused

    def handle_keypress(self, event):
        if not self.game_active or self.game_logic.game_over:
            if event.keysym.lower() == 'p' and self.game_active and not self.game_logic.game_over:
                 self.ui.toggle_pause_button()
            return

        if self.game_logic.paused: # Don't process game moves if paused, only unpause
            if event.keysym.lower() == 'p':
                self.ui.toggle_pause_button() # This will call self.toggle_pause
            return

        key = event.keysym.lower()
        action_taken = False
        if key == 'left' or key == 'a':
            action_taken = self.game_logic.move(-1, 0)
        elif key == 'right' or key == 'd':
            action_taken = self.game_logic.move(1, 0)
        elif key == 'down' or key == 's':
            action_taken = self.game_logic.move(0, 1)
            if action_taken: # If soft drop was successful, reset fall timer for next natural fall
                if self.fall_timer_id: self.ui.after_cancel(self.fall_timer_id)
                self.schedule_next_fall() 
        elif key == 'up' or key == 'w' or key == 'r':
            self.game_logic.rotate_piece()
            action_taken = True # Rotation is an action
        elif key == 'space':
            self.game_logic.hard_drop() # This will lock the piece
            action_taken = True # Hard drop is a significant action
            # Fall timer will be reset by game_loop_step or next lock
        elif key == 'p':
            self.ui.toggle_pause_button() # Calls self.toggle_pause

        if action_taken or key in ['up', 'w', 'r', 'space']: # Update UI after any move/rotation/drop
            self.update_ui_elements()


    def game_loop_step(self):
        if not self.game_active or self.game_logic.paused or self.game_logic.game_over:
            if self.game_logic.game_over and self.game_active:
                self.handle_game_over()
            return

        self.game_logic.fall() # Automatic fall
        self.update_ui_elements()

        if self.game_logic.game_over: # Check again after fall
            self.handle_game_over()
            return

        self.schedule_next_fall() # Schedule the next automatic fall

    def handle_game_over(self):
        print("Game Over!")
        self.game_active = False
        if self.fall_timer_id:
            self.ui.after_cancel(self.fall_timer_id)
            self.fall_timer_id = None
        self.ui.show_game_over_message(self.game_logic.score)
        self.ui.enable_game_controls(game_is_running=False)
        # Final draw to ensure board is up-to-date before game over message
        current_game_surface = self.game_logic.draw(self.game_logic.surface)
        self.ui.update_game_canvas(current_game_surface)


    def schedule_next_fall(self):
        if self.game_active and not self.game_logic.paused and not self.game_logic.game_over:
            # Cancel previous timer if any, to prevent multiple loops if logic changes fall_delay rapidly
            if self.fall_timer_id:
                self.ui.after_cancel(self.fall_timer_id)
            self.fall_timer_id = self.ui.after(self.game_logic.fall_delay, self.game_loop_step)
            self.ui.fall_timer_id = self.fall_timer_id # Share with UI for potential cleanup on close

    def update_ui_elements(self):
        current_game_surface = self.game_logic.draw(self.game_logic.surface)
        self.ui.update_game_canvas(current_game_surface)

        self.ui.update_score_display(self.game_logic.score)
        self.ui.update_level_display(self.game_logic.level)
        self.ui.draw_next_piece(self.game_logic.next_piece)

        # Check and display rewards
        new_reward_messages = self.game_logic.check_and_trigger_rewards()
        if new_reward_messages:
            self.ui.update_rewards_display(new_reward_messages)


    def run(self):
        self.ui.enable_game_controls(game_is_running=False) # Initial state
        self.update_ui_elements() # Show empty board, initial score/level
        try:
            self.ui.mainloop()
        finally:
            if self.fall_timer_id: # Ensure timer is cancelled if window is closed abruptly
                try:
                    self.ui.after_cancel(self.fall_timer_id)
                except Exception: # Tkinter might be destroyed
                    pass
            pygame.quit()
            print("Application closed.")


if __name__ == "__main__":
    app_runner = GameRunner()
    app_runner.run()
