***CTk Sharp Tetris***
A modern, modular implementation of the classic Tetris game using pygame for rendering and customtkinter for the user interface.

***Features***
Classic Tetris gameplay mechanics.

Responsive GUI built with customtkinter.

Real-time rendering of the game using pygame.

Preview of the next Tetris piece.

Score and level tracking.

Achievement/reward system with display.

Play/pause/reset controls.

Keyboard controls for game interaction.

***Files Overview***
main.py: Entry point of the application. Initializes the game and UI.

config.py: Configuration constants used across the app (window sizes, colors, game settings).

game.py: Core Tetris game logic — handles the board, piece movement, collision detection, scoring, and game progression.

ui.py: Defines the TetrisUI class with a rich GUI using customtkinter. Integrates the game logic with the interface.

***Requirements***
Python 3.9+

pygame

customtkinter

Pillow

***Install dependencies via pip:***

pip install pygame customtkinter pillow
Running the Game
bash
Copy
Edit
python main.py

***Controls***
← and →: Move piece left or right

↑: Rotate piece

↓: Soft drop

Space: Hard drop

P: Pause/Resume