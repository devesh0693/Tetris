# ui.py
# (YYYY-MM-DD): 2025-05-10 - CustomTkinter UI elements for Tetris
# (YYYY-MM-DD): 2025-05-11 - Refined next_piece drawing, added rewards display label

import customtkinter as ctk
from PIL import Image # No ImageTk needed if using CTkImage directly with PIL.Image
from config import *

class TetrisUI(ctk.CTk):
    def __init__(self, game_instance_provider, start_game_cb, pause_game_cb, reset_game_cb, handle_input_cb):
        super().__init__()

        self.game_instance_provider = game_instance_provider
        self.start_game_callback = start_game_cb
        self.pause_game_callback = pause_game_cb
        self.reset_game_callback = reset_game_cb
        self.handle_input_callback = handle_input_cb

        self.title("CTk Sharp Tetris")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=3) # Game area larger proportion
        self.grid_columnconfigure(1, weight=1) # Info panel
        self.grid_rowconfigure(0, weight=1)

        self.game_frame = ctk.CTkFrame(self, width=PYGAME_SURFACE_WIDTH, height=PYGAME_SURFACE_HEIGHT,
                                       fg_color=("gray75", "gray25"))
        self.game_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.game_frame.pack_propagate(False) # Prevent resizing from label

        self.game_canvas_label = ctk.CTkLabel(self.game_frame, text="", corner_radius=5)
        self.game_canvas_label.pack(expand=True, fill="both", padx=5, pady=5)
        self.current_ctk_image = None

        self.info_frame = ctk.CTkFrame(self, width=INFO_AREA_WIDTH, corner_radius=10)
        self.info_frame.grid(row=0, column=1, padx=(0,10), pady=10, sticky="nsew")
        self.info_frame.grid_propagate(False)

        # Score
        self.score_label_title = ctk.CTkLabel(self.info_frame, text="Score", font=ctk.CTkFont(size=20, weight="bold"))
        self.score_label_title.pack(pady=(15,0), padx=10)
        self.score_var = ctk.StringVar(value="0")
        self.score_display = ctk.CTkLabel(self.info_frame, textvariable=self.score_var, font=ctk.CTkFont(size=28))
        self.score_display.pack(pady=(0,10), padx=10)

        # Level
        self.level_label_title = ctk.CTkLabel(self.info_frame, text="Level", font=ctk.CTkFont(size=20, weight="bold"))
        self.level_label_title.pack(pady=(10,0), padx=10)
        self.level_var = ctk.StringVar(value="1")
        self.level_display = ctk.CTkLabel(self.info_frame, textvariable=self.level_var, font=ctk.CTkFont(size=28))
        self.level_display.pack(pady=(0,10), padx=10)

        # Next Piece
        self.next_piece_label_title = ctk.CTkLabel(self.info_frame, text="Next", font=ctk.CTkFont(size=18, weight="bold"))
        self.next_piece_label_title.pack(pady=(10,5), padx=10)
        
        # Calculate dynamic size for next piece frame based on BLOCK_SIZE
        # Max 4 blocks wide/high for any piece. Add padding.
        next_piece_canvas_dim = int(4.5 * BLOCK_SIZE * 0.7) # Scaled block size + padding
        self.next_piece_outer_frame = ctk.CTkFrame(self.info_frame, 
                                                 width=next_piece_canvas_dim + 10, # Outer frame for centering
                                                 height=next_piece_canvas_dim + 10)
        self.next_piece_outer_frame.pack(pady=(0,10))
        self.next_piece_outer_frame.pack_propagate(False) # Prevent resizing

        self.next_piece_canvas = ctk.CTkCanvas(self.next_piece_outer_frame,
                                               width=next_piece_canvas_dim,
                                               height=next_piece_canvas_dim,
                                               bg=self.next_piece_outer_frame.cget("fg_color")[0],
                                               highlightthickness=0)
        self.next_piece_canvas.place(relx=0.5, rely=0.5, anchor="center")


        # Rewards Display
        self.rewards_label_title = ctk.CTkLabel(self.info_frame, text="Achievements", font=ctk.CTkFont(size=16, weight="bold"))
        self.rewards_label_title.pack(pady=(15,5), padx=10)
        self.rewards_message_var = ctk.StringVar(value="Keep Playing!")
        self.rewards_display_label = ctk.CTkLabel(self.info_frame, textvariable=self.rewards_message_var,
                                                 font=ctk.CTkFont(size=12), wraplength=INFO_AREA_WIDTH - 20,
                                                 justify="left")
        self.rewards_display_label.pack(pady=(0,10), padx=10, fill="x")


        # Buttons (Grouped in a frame for better spacing)
        self.button_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.button_frame.pack(pady=15, padx=20, fill="x", side="bottom")

        self.start_button = ctk.CTkButton(self.button_frame, text="Start Game", command=self.start_game_callback, font=ctk.CTkFont(size=16))
        self.start_button.pack(pady=5, fill="x", ipady=4)

        self.pause_button = ctk.CTkButton(self.button_frame, text="Pause", command=self.toggle_pause_button, font=ctk.CTkFont(size=16), state="disabled")
        self.pause_button.pack(pady=5, fill="x", ipady=4)

        self.reset_button = ctk.CTkButton(self.button_frame, text="Reset Game", command=self.reset_game_callback, font=ctk.CTkFont(size=16), state="disabled")
        self.reset_button.pack(pady=5, fill="x", ipady=4)

        # Instructions
        instructions_text = "Controls:\n← Left  → Right\n↓ Soft Drop   ↑ Rotate\nSpace Hard Drop\nP Pause/Resume"
        self.instructions_label = ctk.CTkLabel(self.info_frame, text=instructions_text, font=ctk.CTkFont(size=11), justify="center", anchor="s")
        self.instructions_label.pack(pady=(10,5), side="bottom", fill="x", padx=10)

        self.bind("<KeyPress>", self.handle_input_callback)
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close
        self.game_over_dialog = None # To keep track of game over dialog


    def on_closing(self):
        # Potentially save game state or settings here if needed in future
        if self.fall_timer_id: # Accessing fall_timer_id from GameRunner via self.master or callback
             # This needs a proper way to access GameRunner's fall_timer_id if mainloop is here.
             # For now, assume GameRunner handles its own cleanup on pygame.quit()
             pass
        self.destroy() # Destroy CTk window
        # Pygame quit will be handled by GameRunner when mainloop exits


    def update_score_display(self, score):
        self.score_var.set(str(score))

    def update_level_display(self, level):
        self.level_var.set(str(level))

    def draw_next_piece(self, piece):
        self.next_piece_canvas.delete("all")
        if not piece: return

        shape_coords = piece.current_shape_coords
        min_r = min(r for r, c in shape_coords)
        max_r = max(r for r, c in shape_coords)
        min_c = min(c for r, c in shape_coords)
        max_c = max(c for r, c in shape_coords)

        shape_height_blocks = max_r - min_r + 1
        shape_width_blocks = max_c - min_c + 1
        
        # Use a consistent block size for preview, ensure it fits the canvas
        canvas_width = self.next_piece_canvas.winfo_width()
        canvas_height = self.next_piece_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1: # Canvas not ready
            self.after(50, lambda p=piece: self.draw_next_piece(p))
            return

        # Calculate block size to fit the piece within the canvas
        # Allow for a small margin (e.g., 0.5 block on each side)
        available_width = canvas_width * 0.9
        available_height = canvas_height * 0.9
        
        preview_block_size_w = available_width / shape_width_blocks
        preview_block_size_h = available_height / shape_height_blocks
        preview_block_size = min(preview_block_size_w, preview_block_size_h, BLOCK_SIZE * 0.7) # Cap max size


        total_shape_width_px = shape_width_blocks * preview_block_size
        total_shape_height_px = shape_height_blocks * preview_block_size

        offset_x = (canvas_width - total_shape_width_px) / 2
        offset_y = (canvas_height - total_shape_height_px) / 2

        for r_offset, c_offset in shape_coords:
            norm_r = r_offset - min_r
            norm_c = c_offset - min_c

            x0 = offset_x + norm_c * preview_block_size
            y0 = offset_y + norm_r * preview_block_size
            x1 = x0 + preview_block_size
            y1 = y0 + preview_block_size
            
            fill_color_hex = "#%02x%02x%02x" % piece.color
            outline_color_hex = "#%02x%02x%02x" % tuple(max(0, comp - 30) for comp in piece.color)

            self.next_piece_canvas.create_rectangle(x0, y0, x1, y1, 
                                                    fill=fill_color_hex, 
                                                    outline=outline_color_hex, width=1)

    def update_game_canvas(self, pygame_surface):
        try:
            img_data = pygame.image.tostring(pygame_surface, "RGB")
            pil_img = Image.frombytes("RGB", pygame_surface.get_size(), img_data)

            frame_width = self.game_canvas_label.winfo_width()
            frame_height = self.game_canvas_label.winfo_height()

            if frame_width <= 1 or frame_height <= 1: return

            img_aspect = pil_img.width / pil_img.height
            frame_aspect = frame_width / frame_height

            if img_aspect > frame_aspect:
                new_width = frame_width
                new_height = int(new_width / img_aspect)
            else:
                new_height = frame_height
                new_width = int(new_height * img_aspect)
            
            if new_width <=0 or new_height <=0: return # Avoid invalid resize

            resized_pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.current_ctk_image = ctk.CTkImage(light_image=resized_pil_img,
                                                  dark_image=resized_pil_img,
                                                  size=(resized_pil_img.width, resized_pil_img.height))
            self.game_canvas_label.configure(image=self.current_ctk_image)
        except Exception as e:
            print(f"Error updating game canvas: {e}")


    def show_game_over_message(self, final_score):
        if self.game_over_dialog and self.game_over_dialog.winfo_exists():
            self.game_over_dialog.destroy() # Close if already open

        self.start_button.configure(state="normal", text="Play Again")
        self.pause_button.configure(state="disabled", text="Pause")
        self.reset_button.configure(state="normal")

        self.game_over_dialog = ctk.CTkToplevel(self)
        self.game_over_dialog.title("Game Over")
        self.game_over_dialog.geometry("300x180")
        self.game_over_dialog.transient(self)
        self.game_over_dialog.grab_set() # Modal
        self.game_over_dialog.attributes("-topmost", True)


        label = ctk.CTkLabel(self.game_over_dialog, text=f"Game Over!\nFinal Score: {final_score}", font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(pady=20, padx=20, expand=True)

        ok_button = ctk.CTkButton(self.game_over_dialog, text="OK", command=self.game_over_dialog.destroy, width=100)
        ok_button.pack(pady=(0,20))
        self.game_over_dialog.after(100, self.game_over_dialog.lift) # Ensure it's on top


    def toggle_pause_button(self):
        is_paused = self.pause_game_callback()
        if is_paused:
            self.pause_button.configure(text="Resume")
        else:
            self.pause_button.configure(text="Pause")

    def enable_game_controls(self, game_is_running=True, game_is_paused=False):
        if game_is_running:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="normal", text="Resume" if game_is_paused else "Pause")
            self.reset_button.configure(state="normal")
        else: # Game not running (initial state or game over)
            self.start_button.configure(state="normal", text="Start Game")
            self.pause_button.configure(state="disabled", text="Pause")
            self.reset_button.configure(state="disabled") # Disabled until game starts, or enabled on game over for explicit reset

    def update_rewards_display(self, reward_messages):
        if reward_messages: # Expecting a list of messages
            # Display the latest reward or cycle through them
            self.rewards_message_var.set("\n".join(reward_messages[-2:])) # Show last 2 new rewards
        # else:
            # self.rewards_message_var.set("Keep playing!") # Or keep last message

