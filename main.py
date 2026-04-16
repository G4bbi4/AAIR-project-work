import matplotlib.pyplot as plt
import numpy as np
import time
import os

AGENTS = [
    ("A", 1, 1),
    ("B", 1, 4),
]

OBJECTS = [
    (7, 0),
    (6, 3),
    (7, 7),
]

DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0)
    }

class Grid:
    """
    Class representing grid world were the objects reside. The grid can contain walls, objects that can be picked, 
    a delivery station and two agents. The agents can move within the grid are tracked through class attributes.
    """

    def __init__(self, size):
        """
        Constructor for Grid class. The grid is initialized with a set of walls, a delivery station and empty lists for agents and objects.
        :param size: number of rows and columns in the desired squared grid
        """
        self.size = size
        self.walls = {
                    (3,0), (3,1), (3,2), (2,2), (4,2), #upper section
                    (3,5), (3,6), (3,7), (2,5), (4,5), #lower section
                    (6,2), (7,2), #upper right side wall
                    (6,5), (7,5)  #lower right side wall
                    }
        self.objects = []
        self.delivery_station = (0,7)
        self.agents = []

    def add_agent(self, agent):
        """
        Adds an agent to the grid. The agent's position is set through the set_position method of the Agent class.

        :param agent: the agent to be added to the grid
        """
        self.agents.append(agent)

    def add_object(self, obj):
        """
        Adds an object to the grid. The object's position is set through the start_position attribute of the Object class.

        :param obj: the object to be added to the grid
        """
        self.objects.append(obj)

    def render(self):
        """
        Renders the grid world. The grid is represented as a 2D list of strings, where each string represents a cell in the grid.
        """
        grid = [['. ' for _ in range(self.size)] for _ in range(self.size)]
        for (wx, wy) in self.walls:
            grid[wy][wx] = 'W '
        
        for obj in self.objects:
            if not obj.picked:
                ox, oy = obj.position
                grid[oy][ox] = 'O '
            else:
                ox, oy = obj.position
                grid[oy][ox] = 'X '

        sx, sy = self.delivery_station
        grid[sy][sx] = 'S '

        for agent in self.agents:
            ax, ay = agent.position
            grid[ay][ax] = f'{agent.id} '
        for row in grid:
            print(" ".join(row))
    
        return grid

class Agent:

    def __init__(self, id):
        """
        Constructor for Agent class. The agent is initialized with an id and a position.

        :param id: the identifier of the agent, also used for rendering the grid
        :param position: the initial position of the agent, set to None until the set_position method is called
        """
        self.id = id
        self.position = None

    def set_position(self, x, y):
        """
        Sets the position of the agent. 
        The method checks if the new position is valid (not a wall and within grid boundaries) before updating the agent's position.

        :param x: x coordinate of the agent's position
        :param y: y coordinate of the agent's position
        """

        if (x, y) in g.walls or x < 0 or x >= g.size or y < 0 or y >= g.size:
            return  # Instead of raising error, stay in the same position
        else:
            self.position = (x, y)

    def get_position(self):
        """
        Returns the current position of the agent.
        """
        return self.position

    def move(self, direction, grid):
        """
        Moves the agent in the specified direction if the new position is valid.
        :param direction: the direction where the agent should move (up, down, left, right)
        :param grid: the grid instance to check for walls and boundaries
        :returns: True if the move was successful (not a wall/out of bounds), False otherwise
        """
        if direction not in DIRECTIONS:
            raise ValueError(f"Direzione sconosciuta: {direction}")
        
        dx, dy = DIRECTIONS[direction]
        curr_x, curr_y = self.position
        new_x, new_y = curr_x + dx, curr_y + dy

        if (new_x, new_y) in grid.walls or new_x < 0 or new_x >= grid.size or new_y < 0 or new_y >= grid.size:
            return (False, (new_x, new_y))  # Move failed, return False and the attempted position
        
        self.set_position(new_x, new_y)
        return (True, (new_x, new_y))  # Move successful, return True and the new position

class Object:

    def __init__(self, start_position, picked = False):
        """
        Constructor for Object class. The object is initialized with a position and a picked status.

        :param start_position: the initial position of the object
        :param picked: the initial picked status of the object
        """
        self.position = start_position
        self.picked = picked

    def set_picked(self, new_picked):
        """
        Sets the picked status of the object.
        :param new_picked: the new picked status of the object, either True or False
        """
        if not isinstance(new_picked, bool):
            raise ValueError("Picked status must be a boolean value.")
        else:
            self.picked = new_picked


class Trainer:
    """
    Centralized Trainer for Multi-Agent Q-learning.
    Manages a single joint Q-table for all agents.
    """
    def __init__(self, grid, alpha=0.1, gamma=0.9, epsilon=0.1):
        #riguarda i valori dei parametri
        self.grid = grid
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        # joint state:
        self.num_states = (grid.size ** 2) ** len(grid.agents)
        # joint actions:
        self.action_names = list(DIRECTIONS.keys())
        self.num_joint_actions = len(self.action_names) ** len(grid.agents)
        # initialize q-table:
        self.q_table = np.zeros((self.num_states, self.num_joint_actions)) # 4096x64

    def get_state_index(self):
        """
        Map joint agent positions to a single state index.
        """
        idx = 0 # idx = pos_agente_0 * 1  +  pos_agente_1 * 64
        coords = []
        for agent in self.grid.agents:
            x, y = agent.position
            pos_idx = y * self.grid.size + x
            coords.append(pos_idx) # avrò ad es: [19, 13]

        shape = (self.grid.size ** 2,) * len(self.grid.agents) # 64x64
        idx = int(np.ravel_multi_index(coords, shape)) #indice dell'elemento [19,13] della tabella 64x64
        return idx
    
    def get_joint_action(self, action_idx):
        """
        Map joint action index back to individual agent actions.
        :param action_idx: the index of the joint action in the Q-table
        """
        shape = (4, 4)
        indices = np.unravel_index(action_idx, shape=shape)
        joint_actions = [self.action_names[i] for i in indices] #lista contenente le azioni da eseguire per ogni agente, ad es: ['down', 'up']
        return joint_actions

    def select_action(self, state_idx):
            """
            Epsilon-greedy action selection.
            :param state_idx: the index of the current state in the Q-table
            """
            if np.random.rand() < self.epsilon:
                return np.random.randint(self.num_joint_actions)
            return np.argmax(self.q_table[state_idx])

    def step(self, joint_action_idx):
        """
        Execute joint action, handle object collection, and check goal.
        """
        actions = self.get_joint_action(joint_action_idx)
        total_reward = 0
        outcome = [] #dove salvo i risultati dei move per ogni agente, così da poter eventualmente assegnare reward per i muri o per le celle vuote
        
        # Apply actions
        for i, agent in enumerate(self.grid.agents):
            outcome.append(agent.move(actions[i]))

        # --- DA METTERE REWARD MURI E REWARD CELLE VUOTE ---
        for agent, (success, attempted_position) in zip(self.grid.agents, outcome):
            if not success:  # se il movimento non è riuscito (muro o fuori dai limiti)
                total_reward -= 1
            else:
                object_picked = False  # flag per verificare se è stato raccolto un oggetto in questo step
                for obj in self.grid.objects:
                    if not obj.picked and agent.position == obj.position:
                        obj.set_picked(True)
                        total_reward += 10   # Reward per ogni oggetto raccolto
                        object_picked = True
                        break
                if not object_picked:
                    total_reward -= 0.04

        # Verifica se tutti gli oggetti sono stati raccolti
        all_collected = all(obj.picked for obj in self.grid.objects)
        reached_goal = False
        if all_collected:
            # Se tutti raccolti, verifica se tutti gli agenti sono sulla delivery station
            all_on_station = all(agent.position == self.grid.delivery_station for agent in self.grid.agents)
            if all_on_station:
                total_reward += 50  # reward per raggiungimento goal
                reached_goal = True

        return total_reward, reached_goal

    def update(self, state, action, reward, next_state): #RICONTROLLA I NOMI DEI PARAMETRI IN INGRESSO
            """Aggiorna la Q-table usando la formula di Q-learning.
            :param state: l'indice dello stato corrente
            :param action: l'indice dell'azione eseguita
            :param reward: la ricompensa ricevuta dopo aver eseguito l'azione
            :param next_state: l'indice dello stato successivo dopo aver eseguito l'azione
            """
            best_next_action = np.argmax(self.q_table[next_state])
            estimated_q_opt = reward + self.gamma * self.q_table[next_state][best_next_action]
            # aggiornamento tabella Q
            self.q_table[state][action] += self.alpha * (estimated_q_opt - self.q_table[state][action])

    def train(self, episodes=1000):
            for ep in range(episodes):
                # Reset agents to start positions (hardcoded for now)
                for i, (name, x, y) in enumerate(AGENTS):
                    self.grid.agents[i].position = (x, y)
                
                # Reset objects picked status
                for obj in self.grid.objects:
                    obj.set_picked(False)
                
                state = self.get_state_index()
                done = False
                steps = 0
                while not done and steps < 100:
                    action = self.select_action(state)
                    reward, done = self.step(action)
                    next_state = self.get_state_index()
                    self.update(state, action, reward, next_state)
                    state = next_state
                    steps += 1
                
                if ep % 100 == 0:
                    print(f"Episode {ep} finished in {steps} steps")

#funzione a se stante (da rivedere se può essere inserita in una classe)
def populate(grid, agents_config, objects_config):
    """
    Function that populates the grid with agents and objects based on the provided configurations.
    :param grid: the grid to be populated
    :param agents_config: a list of tuples, where each tuple contains the id, x and y coordinates of an agent
    :param objects_config: a list of tuples, where each tuple contains the x and y coordinates of an object
    """
    for agent_id, x, y in agents_config:
        agent = Agent(agent_id)
        agent.set_position(x, y)
        grid.add_agent(agent)
    
    for x, y in objects_config:
        obj = Object((x, y))
        grid.add_object(obj)


if __name__ == "__main__":
    g = Grid(8)
    populate(g, AGENTS, OBJECTS)
    print('Initial grid:')
    g.render()

    trainer = Trainer(g)
    print("Starting Centralized Training...")
    trainer.train(episodes=501)

 # Show final result
    print("Final demo run:")
    for i, (name, x, y) in enumerate(AGENTS):
        g.agents[i].position = (x, y)
    
    state = trainer.get_state_index()
    for _ in range(10):
        os.system('clear')
        g.render()
        action = np.argmax(trainer.q_table[state])
        trainer.step(action)
        state = trainer.get_state_index()
        time.sleep(0.5)
        if any(a.position == g.delivery_station for a in g.agents):
            os.system('clear')
            g.render()
            print("Goal Reached!")
            break
    
    # Animazione: muovi l'agente A verso destra per 3 passi
    for _ in range(5):
        try:
            g.agents[0].move("down")  # Muovi l'agente A a destra
        except ValueError:
            break  # Se non può muoversi, interrompi
        
        time.sleep(0.5)  # Ritardo di 0.5 secondi
        os.system('clear')  # Cancella lo schermo (su Linux/Mac; usa 'cls' su Windows)
        g.render()  # Ristampa la griglia aggiornata
    
    print("Animazione completata.")