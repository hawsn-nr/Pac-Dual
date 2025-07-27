# server.py
import socket
import pickle
import threading
import time
import random
from Ghost import NPCGhost

HOST = '127.0.0.1'
PORT = 65432
TILE_SIZE = 20
MAZE_LAYOUT = [
    "############################", "#............##............#", "#.####.#####.##.#####.####.#", "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#", "#..........................#", "#.####.##.########.##.####.#", "#.####.##.########.##.####.#",
    "#......##....##....##......#", "######.##### ## #####.######", "     #.##### ## #####.#     ", "     #.##          ##.#     ",
    "     #.## ###--### ##.#     ", "######.## #      # ##.######", "      .   #      #   .      ", "######.## #      # ##.######",
    "     #.## ######## ##.#     ", "     #.##          ##.#     ", "     #.## ######## ##.#     ", "######.## ######## ##.######",
    "#............##............#", "#.####.#####.##.#####.####.#", "#.####.#####.##.#####.####.#", "#o..##................##..o#",
    "###.##.##.########.##.##.###", "#...##.##.########.##.##...#", "#..........................#", "#.##########.##.##########.#",
    "#.##########.##.##########.#", "#..........................#", "############################"
]
WIDTH, HEIGHT = len(MAZE_LAYOUT[0]) * TILE_SIZE, len(MAZE_LAYOUT) * TILE_SIZE
dots = {0: [], 1: []}
for r, row in enumerate(MAZE_LAYOUT):
    for c, tile in enumerate(row):
        if tile in ['.', 'o']:
            pos = (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2)
            if c < len(row) / 2: dots[0].append(pos)
            else: dots[1].append(pos)

npc_ghosts = [
    NPCGhost(13 * TILE_SIZE + TILE_SIZE // 2, 11 * TILE_SIZE + TILE_SIZE // 2),
    NPCGhost(6 * TILE_SIZE + TILE_SIZE // 2, 5 * TILE_SIZE + TILE_SIZE // 2),
    NPCGhost(21 * TILE_SIZE + TILE_SIZE // 2, 5 * TILE_SIZE + TILE_SIZE // 2),
    NPCGhost(21 * TILE_SIZE + TILE_SIZE // 2, 20 * TILE_SIZE + TILE_SIZE // 2)
]

game_state = {'players': {}, 'dots': dots, 'npc_ghosts': [g.get_pos() for g in npc_ghosts], 'game_over': None, 'maze_layout': MAZE_LAYOUT, 'tile_size': TILE_SIZE}
connections = []
lock = threading.Lock()
PLAYER_RADIUS = TILE_SIZE // 2 - 3
def get_tile(x, y):
    c = int(x // TILE_SIZE)
    r = int(y // TILE_SIZE)
    if 0 <= r < len(MAZE_LAYOUT) and 0 <= c < len(MAZE_LAYOUT[0]):
        return MAZE_LAYOUT[r][c]
    return '#'
def can_move(x, y, dx, dy, entity_type='player'):
    radius = PLAYER_RADIUS
    next_x, next_y = x + dx, y + dy
    corners = [(next_x + radius, next_y + radius), (next_x - radius, next_y + radius),
               (next_x + radius, next_y - radius), (next_x - radius, next_y - radius)]
    for cx, cy in corners:
        tile = get_tile(cx, cy)
        if tile == '#': return False
        if tile == '-' and entity_type == 'player': return False
    return True
def update_player_position(player_data):
    pos = player_data['pos']
    speed = player_data['speed']
    vel = player_data.get('velocity', (0,0))
    desired_vel = player_data.get('desired_velocity', (0,0))
    is_aligned = (pos[0] % TILE_SIZE == TILE_SIZE // 2) and (pos[1] % TILE_SIZE == TILE_SIZE // 2)
    if is_aligned:
        if desired_vel != (0,0) and can_move(pos[0], pos[1], desired_vel[0], desired_vel[1]):
            vel = desired_vel
    if can_move(pos[0], pos[1], vel[0], vel[1]):
        player_data['pos'] = (pos[0] + vel[0], pos[1] + vel[1])
        player_data['velocity'] = vel
    else:
        reversed_velocity = (-vel[0], -vel[1])
        player_data['velocity'] = reversed_velocity
        player_data['desired_velocity'] = reversed_velocity
def update_ghosts():
    target_player_pos = None
    for p_data in game_state['players'].values():
        if not p_data['is_ghost']:
            target_player_pos = p_data['pos']
            break
    if not target_player_pos:
        target_player_pos = (WIDTH / 2, HEIGHT / 2)
    for i, ghost in enumerate(npc_ghosts):
        pos, speed = ghost.get_pos(), ghost.speed
        is_stuck = not can_move(pos[0], pos[1], ghost.dx, ghost.dy, 'ghost')
        is_aligned = (pos[0] % TILE_SIZE == TILE_SIZE // 2) and (pos[1] % TILE_SIZE == TILE_SIZE // 2)
        if is_stuck or is_aligned:
            preferences = []
            if i == 0:
                if target_player_pos[0] > pos[0]: preferences.append((speed, 0))
                if target_player_pos[0] < pos[0]: preferences.append((-speed, 0))
                if target_player_pos[1] > pos[1]: preferences.append((0, speed))
                if target_player_pos[1] < pos[1]: preferences.append((0, -speed))
            elif i == 1:
                dx, dy = abs(target_player_pos[0] - pos[0]), abs(target_player_pos[1] - pos[1])
                if dx < dy: preferences.append((0, speed if target_player_pos[1] > pos[1] else -speed))
                else: preferences.append((speed if target_player_pos[0] > pos[0] else -speed, 0))
            elif i == 3:
                dist_sq = (target_player_pos[0] - pos[0])**2 + (target_player_pos[1] - pos[1])**2
                is_close = dist_sq < (8 * TILE_SIZE)**2
                if (is_close and target_player_pos[0] > pos[0]) or (not is_close and target_player_pos[0] < pos[0]): preferences.append((-speed, 0))
                if (is_close and target_player_pos[0] < pos[0]) or (not is_close and target_player_pos[0] > pos[0]): preferences.append((speed, 0))
                if (is_close and target_player_pos[1] > pos[1]) or (not is_close and target_player_pos[1] < pos[1]): preferences.append((0, -speed))
                if (is_close and target_player_pos[1] < pos[1]) or (not is_close and target_player_pos[1] > pos[1]): preferences.append((0, speed))
            possible_moves = []
            all_directions = [(speed, 0), (-speed, 0), (0, speed), (0, -speed)]
            for move in all_directions:
                if can_move(pos[0], pos[1], move[0], move[1], 'ghost'):
                    possible_moves.append(move)
            best_move = None
            for pref_move in preferences:
                if pref_move in possible_moves:
                    best_move = pref_move
                    break
            if not best_move and possible_moves:
                best_move = random.choice(possible_moves)
            if best_move:
                ghost.dx, ghost.dy = best_move
        if can_move(pos[0], pos[1], ghost.dx, ghost.dy, 'ghost'):
            ghost.move()
def server_logic_update():
    while True:
        with lock:
            if game_state['game_over']: break
            for player_data in game_state['players'].values():
                update_player_position(player_data)
            update_ghosts()
            game_state['npc_ghosts'] = [g.get_pos() for g in npc_ghosts]
            check_game_rules()
        time.sleep(0.035)
def check_game_rules():
    if game_state['game_over']: return
    players_data = game_state['players']
    if len(players_data) < 2: return
    p0, p1 = players_data[0], players_data[1]
    boundary_x = WIDTH / 2
    p0['is_ghost'] = p0['pos'][0] > boundary_x
    p1['is_ghost'] = p1['pos'][0] < boundary_x
    collision_dist_sq = (PLAYER_RADIUS * 1.5) ** 2 
    dot_collision_dist_sq = PLAYER_RADIUS ** 2
    for p_id, player in players_data.items():
        if player['is_ghost']: continue
        dots_to_check = game_state['dots'][p_id]
        dots_eaten = [d for d in dots_to_check if ((player['pos'][0]-d[0])**2 + (player['pos'][1]-d[1])**2) < dot_collision_dist_sq]
        if dots_eaten:
            game_state['dots'][p_id] = [d for d in dots_to_check if d not in dots_eaten]
            player['score'] += len(dots_eaten) * 10
            if not game_state['dots'][p_id]:
                game_state['game_over'] = f"Player {p_id} wins by collecting all dots!"
                return
        for ghost_pos in game_state['npc_ghosts']:
            if ((player['pos'][0]-ghost_pos[0])**2 + (player['pos'][1]-ghost_pos[1])**2) < collision_dist_sq:
                game_state['game_over'] = f"Player {1-p_id} wins! Player {p_id} was caught."
                return
    if p0['is_ghost'] and not p1['is_ghost']:
        if ((p0['pos'][0]-p1['pos'][0])**2 + (p1['pos'][1]-p1['pos'][1])**2) < collision_dist_sq:
            game_state['game_over'] = "Player 0 wins by capturing Player 1!"
            return
    if p1['is_ghost'] and not p0['is_ghost']:
        if ((p1['pos'][0]-p0['pos'][0])**2 + (p1['pos'][1]-p0['pos'][1])**2) < collision_dist_sq:
            game_state['game_over'] = "Player 1 wins by capturing Player 0!"
            return
def client_thread(conn, player_id):
    player_speed = 2.0 
    start_pos = (1 * TILE_SIZE + TILE_SIZE // 2, 25 * TILE_SIZE + TILE_SIZE // 2) if player_id == 0 \
        else (26 * TILE_SIZE + TILE_SIZE // 2, 25 * TILE_SIZE + TILE_SIZE // 2)
    initial_velocity = (player_speed, 0) if player_id == 0 else (-player_speed, 0)
    with lock:
        game_state['players'][player_id] = {'pos': start_pos, 'score': 0, 'is_ghost': False, 'speed': player_speed, 'velocity': initial_velocity, 'desired_velocity': initial_velocity}
    conn.send(pickle.dumps({'id': player_id, 'maze': MAZE_LAYOUT, 'tile_size': TILE_SIZE, 'speed': player_speed}))
    while True:
        try:
            data = pickle.loads(conn.recv(2048))
            with lock:
                if player_id in game_state['players']:
                    game_state['players'][player_id]['desired_velocity'] = data['vel']
            conn.sendall(pickle.dumps(game_state))
        except: break
    with lock:
        if conn in connections: connections.remove(conn)
        if player_id in game_state['players']: del game_state['players'][player_id]
        if not game_state['game_over']: game_state['game_over'] = "Opponent disconnected."
    conn.close()
def start_server():
    global WIDTH, HEIGHT
    WIDTH = len(MAZE_LAYOUT[0]) * TILE_SIZE
    HEIGHT = len(MAZE_LAYOUT) * TILE_SIZE
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(2)
        print(f"Server started on {HOST}:{PORT}")
        logic_thread = threading.Thread(target=server_logic_update)
        logic_thread.daemon = True
        logic_thread.start()
        player_count = 0
        while len(connections) < 2:
            conn, addr = s.accept()
            connections.append(conn)
            thread = threading.Thread(target=client_thread, args=(conn, player_count))
            thread.daemon = True
            thread.start()
            player_count += 1
        print("Game is starting!")
        while len(connections) > 0: time.sleep(1)
        print("Game over.")
if __name__ == "__main__":
    start_server()