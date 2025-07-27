import socket
import pickle
from Ui import GameUI

UPDATE_DELAY_MS = 16

class Network:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.initial_data = None
    def connect(self):
        try:
            self.client.connect((self.host, self.port))
            self.initial_data = pickle.loads(self.client.recv(4096))
            return True
        except: return False
    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(4096))
        except: return None

class ClientGame:
    def __init__(self, host, port):
        self.network = Network(host, port)
        self.game_running = False
        self.desired_velocity = (0, 0)

    def start(self):
        if not self.network.connect():
            print("Could not connect to server.")
            return
        init_data = self.network.initial_data
        player_id = init_data['id']
        maze_layout = init_data['maze']
        tile_size = init_data['tile_size']
        self.player_speed = init_data['speed']
        self.ui = GameUI(f"Pac-Dual - Player {player_id}", maze_layout, tile_size)
        self.ui.set_key_bindings(self.on_key_press)
        self.ui.set_on_closing(self.on_closing)
        self.game_running = True
        self.game_loop()
        self.ui.start_loop()

    def on_key_press(self, event):
        if event.keysym == "Left": self.desired_velocity = (-self.player_speed, 0)
        elif event.keysym == "Right": self.desired_velocity = (self.player_speed, 0)
        elif event.keysym == "Up": self.desired_velocity = (0, -self.player_speed)
        elif event.keysym == "Down": self.desired_velocity = (0, self.player_speed)

    def on_closing(self):
        self.game_running = False
        self.ui.destroy()

    def game_loop(self):
        if not self.game_running: return
        game_state = self.network.send({'vel': self.desired_velocity})
        if game_state:
            self.ui.draw_game_state(game_state, self.network.initial_data['id'])
            if game_state.get('game_over'): self.game_running = False
        else:
            print("Connection lost.")
            self.game_running = False
        if self.game_running:
            self.ui.schedule_update(UPDATE_DELAY_MS, self.game_loop)
            
if __name__ == "__main__":
    client_game = ClientGame('127.0.0.1', 65432)
    client_game.start()