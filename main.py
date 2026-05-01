import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
from matplotlib.animation import PillowWriter
from matplotlib.animation import FFMpegWriter
import numpy as np
import time
import os
import sys

class Tee:
    def __init__(self, filename):
        self.file = open(filename, 'w')
        self.stdout = sys.stdout
    def write(self, data):
        self.stdout.write(data)
        self.file.write(data)
    def flush(self):
        self.stdout.flush()
        self.file.flush()

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
        
    #dovrebbe andare bene qui MA FORSE E' RIDONDANTE CON QUELLA SOPRA
    def populate(self, agents_config, objects_config):
        """
        Function that populates the grid with agents and objects based on the provided configurations.
        :param grid: the grid to be populated
        :param agents_config: a list of tuples, where each tuple contains the id, x and y coordinates of an agent
        :param objects_config: a list of tuples, where each tuple contains the x and y coordinates of an object
        """
        for agent_id, x, y in agents_config:
            agent = Agent(agent_id)
            agent.set_position(x, y, self) #con self passo la griglia
            self.add_agent(agent)
        
        for x, y in objects_config:
            obj = Object((x, y))
            self.add_object(obj)

    def plot_grid(self, fig = None, ax = None):
        """
        Plots the grid using patches for walls, station, objects, and agents.
        """
        if fig is None or ax is None:
            fig, ax = plt.subplots(figsize = (8, 8))

        # Set axis limits and appearance
        ax.set_xlim(0, self.size )
        ax.set_ylim(self.size, 0)
        ax.set_aspect('equal')
        ax.set_xticklabels([])   # rimuove etichette X
        ax.set_yticklabels([])   # rimuove etichette Y
        ax.grid(color = 'black', linewidth = 1)

        # Plot walls
        for (wx, wy) in self.walls:
            ax.add_patch(mpatches.Rectangle((wx, wy), 1, 1, facecolor='#CE3018', edgecolor='white', hatch='//'))

        # Plot delivery station
        sx, sy = self.delivery_station
        ax.plot(sx + 0.5, sy + 0.5, marker='*', markersize=40, markerfacecolor='green', markeredgecolor='black')

        # Plot objects
        for obj in self.objects:
            if not obj.picked:
                ox, oy = obj.position
                ax.add_patch(mpatches.Circle((ox + 0.5, oy + 0.5), 0.3, facecolor='#03C03C', edgecolor='black'))
            else:
                ox, oy = obj.position
                ax.plot(ox + 0.5, oy + 0.5, marker='X', markersize=35, markerfacecolor='#03C03C', markeredgecolor='black')
        
        # Plot agents
        for agent in self.agents:
            ax.add_patch(mpatches.Circle((agent.position[0] + 0.5, agent.position[1] + 0.5), 0.35, color='darkblue'))
            ax.text(agent.position[0] + 0.5, agent.position[1] + 0.5, agent.id, color='white', ha='center', va='center', fontsize=12, weight='bold')

        return fig, ax

    def reset_grid(self):
        """
        Resets the grid to its initial state.
        """

        # Reset agents to start positions
        for i, (name, x, y) in enumerate(AGENTS):
            self.agents[i].position = (x, y)
        
        # Reset objects picked status
        for obj in self.objects:
            obj.set_picked(False)


class Agent:

    def __init__(self, id):
        """
        Constructor for Agent class. The agent is initialized with an id and a position.

        :param id: the identifier of the agent, also used for rendering the grid
        :param position: the initial position of the agent, set to None until the set_position method is called
        """
        self.id = id
        self.position = None

    def set_position(self, x, y, grid):
        """
        Sets the position of the agent. 
        The method checks if the new position is valid (not a wall and within grid boundaries) before updating the agent's position.

        :param grid: the grid instance
        :param x: x coordinate of the agent's position
        :param y: y coordinate of the agent's position
        """

        if (x, y) in grid.walls or x < 0 or x >= grid.size or y < 0 or y >= grid.size:
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
        
        self.set_position(new_x, new_y, grid)
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
    def __init__(self, grid, c1=1, c2=1, gamma=0.9): #PROVA A VARIARE GAMMA
        #riguarda i valori dei parametri
        self.grid = grid
        self.t = 0 #numero di passi totali, usato per decrescere alpha nel tempo
        self.c1 = c1
        self.c2 = c2
        self.alpha = self.c1 / (self.c2 + self.t)
        self.gamma = gamma
        self.epsilon = 0.1
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

        #shape = (self.grid.size ** 2,) * len(self.grid.agents) # 64x64
        #idx = int(np.ravel_multi_index(coords, shape)) #indice dell'elemento [19,13] della tabella 64x64
        idx = coords[0] + coords[1] * (self.grid.size ** 2)
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
                action = np.random.randint(self.num_joint_actions)

                # if self.t > 0:
                #     self.epsilon = 1 / self.t
                
                return action
            
            else:
                action = np.argmax(self.q_table[state_idx])
                # q_values = self.q_table[state_idx]
                # max_q = np.max(q_values)
                # best_actions = np.where(q_values == max_q)[0]
                # action = np.random.choice(best_actions)

                # if self.t > 0:
                #     self.epsilon = 1 / self.t

                return action

    def step(self, joint_action_idx):
        """
        Execute joint action, handle object collection, and check goal.
        :param joint_action_idx: the index of the joint action to be executed
        """
        actions = self.get_joint_action(joint_action_idx)
        total_reward = 0
        outcome = [] #dove salvo i risultati dei move per ogni agente, così da poter eventualmente assegnare reward per i muri o per le celle vuote
        
        # Apply actions
        for i, agent in enumerate(self.grid.agents):
            outcome.append(agent.move(actions[i], self.grid))

        # --- DA METTERE REWARD MURI E REWARD CELLE VUOTE ---
        for agent, (success, attempted_position) in zip(self.grid.agents, outcome):
            if not success:  # se il movimento non è riuscito (muro o fuori dai limiti)
                total_reward -= 0.5
            else:
                is_picked = False  # flag per verificare se è stato raccolto un oggetto in questo step
                for obj in self.grid.objects:
                    if not obj.picked and agent.position == obj.position:
                        obj.set_picked(True)
                        total_reward += 10   # Reward per ogni oggetto raccolto
                        is_picked = True
                        break
                if not is_picked:
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
            """
            Aggiorna la Q-table usando la formula di Q-learning.
            :param state: l'indice dello stato corrente
            :param action: l'indice dell'azione eseguita
            :param reward: la ricompensa ricevuta dopo aver eseguito l'azione
            :param next_state: l'indice dello stato successivo dopo aver eseguito l'azione
            """

            self.t += 1
            self.alpha = self.c1 / (self.c2 + self.t)

            best_next_action = np.argmax(self.q_table[next_state])
            estimated_q_opt = reward + self.gamma * self.q_table[next_state][best_next_action]

            # aggiornamento tabella Q
            self.q_table[state][action] += self.alpha * (estimated_q_opt - self.q_table[state][action])

    def train(self, episodes, decay_rate):
            """
            Esegue il processo di training per un numero specificato di episodi.
            :param episodes: il numero di episodi di training da eseguire
            :param decay_rate: il tasso di decadimento dell'epsilon
            """
            for ep in range(episodes):

                self.grid.reset_grid()  # Resetta la griglia all'inizio di ogni episodio
                

                self.epsilon = max(0.01, self.epsilon * decay_rate)
                 
                state = self.get_state_index()
                done = False
                steps = 0
                while not done and steps < 100000:
                    action = self.select_action(state)
                    reward, done = self.step(action)
                    next_state = self.get_state_index()
                    self.update(state, action, reward, next_state)
                    state = next_state
                    steps += 1
                
                #self.grid.render()
                print(f"Episode {ep} finished in {steps} steps, epsilon: {self.epsilon:.16f}")

    def animate_grid(self, interval=100, repeat=True, max_steps=5000):
        """
        Funzione che esegue una animazione attraverso FuncAnimation
        """
        fig, ax = plt.subplots(figsize=(5, 5))  # figura più piccola
        self.grid.reset_grid()

        done = False
        steps = 0

        def update(frame):
            nonlocal done, steps
            ax.clear()
            # Primo frame: mostra solo lo stato iniziale, nessuna azione
            if frame == 0:
                self.grid.plot_grid(fig=fig, ax=ax)
                return []
            if done or steps >= max_steps:
                if anim.event_source is not None:
                    anim.event_source.stop()
                return []
            state = self.get_state_index()
            action = np.argmax(self.q_table[state]) #+ np.random.randn(self.num_joint_actions) * 1e-7
            reward, done = self.step(action)
            steps += 1
            self.grid.plot_grid(fig=fig, ax=ax)
            return []

        anim = FuncAnimation(fig=fig, func=update, frames=range(max_steps+1), interval=interval, repeat=repeat)
        return anim


if __name__ == "__main__":

    sys.stdout = Tee("training_log.txt") 

    # - - - HYPERPARAMETERS CONFIGURATION - - -
    
    HP_C1 = 1
    HP_C2 = 1
    HP_GAMMA = 0.9
    HP_EPISODES = 1000
    
    g = Grid(8)
    g.populate(AGENTS, OBJECTS)
    g.objects[0].set_picked(True)
    print('Initial grid:')
    # fig,ax =g.plot_grid()
    # plt.show()
    g.render()

    trainer = Trainer(g, c1=HP_C1, c2=HP_C2, gamma=HP_GAMMA)
    # - - - TRAINING - - -

    # print(f"Hyperparameters: c1={HP_C1}, c2={HP_C2}, gamma={HP_GAMMA}")
    # print(f"Starting Centralized Training with c1={trainer.c1}, c2={trainer.c2}, gamma={trainer.gamma}...")
    # trainer.train(episodes = HP_EPISODES, decay_rate=0.99)

    # - - - Q-TABLE SAVE/LOAD - - -

    # np.save('q_table.npy', trainer.q_table)
    # print("Q-table salvata in q_table.npy")
    
    #Per caricare in seguito:
    q_table = np.load('q_table.npy')

    # - - - ANIMAZIONE - - -

    #g.reset_grid()
    #anim = trainer.animate_grid()
    # Salva animazione come GIF (opzionale)
    #anim.save('Q_learning_grid.gif', writer=PillowWriter(fps=2, bitrate=1000), dpi=100)

    # Salva animazione come MP4 usando FFMpegWriter esplicito
    #anim.save('Q_learning_grid.mp4', writer=FFMpegWriter(fps=5, bitrate=1000), dpi=100)
    
    #anim.save('prova.mp4', writer=FFMpegWriter(fps=5, bitrate=1000), dpi=100)

    
    # - - - DEMO TEST - - -

    g.reset_grid()

    done = False
    steps = 0
    print("Starting demo ...")
    while not done and steps < 5000:
        state = trainer.get_state_index()
        action = np.argmax(trainer.q_table[state] + np.random.randn(trainer.num_joint_actions) * 1e-3)  # con rumore gaussiano
        reward, done = trainer.step(action)
        steps += 1
        #os.system('clear')
        # g.render()
        # print(f"Epsilon finale: {trainer.epsilon:.16f}")
        # print(f"State: {state}")
        # print(f"Steps: {steps}")
        # time.sleep(0.15)
    
    if done:
        print(f"Goal Reached in {steps} steps!")
    else:
        print("Demo completed without reaching the goal.")

    #RICORDARSI DI TOGLIERE RENDER E PRINT VARI 
