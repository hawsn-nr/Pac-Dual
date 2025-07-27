import tkinter as tk

class GameUI:
    BG_COLOR = "black"
    PLAYER_COLOR = "yellow"
    OPPONENT_COLOR = "cyan"
    GHOST_PLAYER_COLOR = "red"
    NPC_GHOST_COLOR = "pink"
    DOT_COLOR = "white"
    WALL_COLOR = "#1919A6"

    def __init__(self, title, maze_layout, tile_size):
        self.maze_layout = maze_layout
        self.tile_size = tile_size
        self.width = len(maze_layout[0]) * tile_size
        self.height = len(maze_layout) * tile_size
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg=self.BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        self._draw_maze()

    def _draw_maze(self):
        for r, row in enumerate(self.maze_layout):
            for c, tile in enumerate(row):
                if tile == '#':
                    x1, y1 = c * self.tile_size, r * self.tile_size
                    x2, y2 = x1 + self.tile_size, y1 + self.tile_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.WALL_COLOR, outline="")

    def draw_game_state(self, state, my_player_id):
        self.canvas.delete("dots", "players", "ghosts", "score", "game_over", "divider")
        self.canvas.create_line(self.width / 2, 0, self.width / 2, self.height, fill="gray25", dash=(4, 4), tags="divider")
        radius = self.tile_size // 2 - 3
        all_dots = state['dots'].get(0, []) + state['dots'].get(1, [])
        for dot_pos in all_dots:
            x, y = dot_pos
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=self.DOT_COLOR, outline="", tags="dots")
        for ghost_pos in state.get('npc_ghosts', []):
            x, y = ghost_pos
            self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=self.NPC_GHOST_COLOR, outline="white", tags="ghosts")
        for p_id, p_data in state['players'].items():
            x, y = p_data['pos']
            is_ghost = p_data.get('is_ghost', False)
            color = self.GHOST_PLAYER_COLOR if is_ghost else (self.PLAYER_COLOR if p_id == my_player_id else self.OPPONENT_COLOR)
            self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=color, outline="white", tags="players")
        p0_score = state['players'].get(0, {}).get('score', 0)
        p1_score = state['players'].get(1, {}).get('score', 0)
        self.canvas.create_text(10, 10, text=f"P0 Score: {p0_score}", fill="white", anchor="nw", font=("Arial", 12), tags="score")
        self.canvas.create_text(self.width - 10, 10, text=f"P1 Score: {p1_score}", fill="white", anchor="ne", font=("Arial", 12), tags="score")
        if state.get('game_over'):
            self.canvas.create_text(self.width/2, self.height/2, text=state['game_over'], font=("Arial", 24, "bold"), fill="green", tags="game_over")

    def set_key_bindings(self, on_press): self.root.bind("<KeyPress>", on_press)
    def set_on_closing(self, on_closing_func): self.root.protocol("WM_DELETE_WINDOW", on_closing_func)
    def schedule_update(self, delay, update_func): self.root.after(delay, update_func)
    def start_loop(self): self.root.mainloop()
    def destroy(self): self.root.destroy()