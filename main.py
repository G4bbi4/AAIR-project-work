import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
from matplotlib.animation import PillowWriter
from matplotlib.animation import FFMpegWriter
import numpy as np
import sys


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
    Class representing a 8x8 grid world. The grid can contain walls, objects that can be picked, 
    a delivery station and two agents.
    """

    def __init__(self, size):
        """
        Constructor for Grid class. The grid is initialized with a set of walls, a delivery station and empty lists for agents and objects.
        
        :param size: number of rows and columns in the desired squared grid
        """
        self.size = size
        self.walls = {
                    (3,0), (3, 1),
                    (0,3), (1,3), (2,3),
                    (3,6), (3,7)
                    }
        self.objects = []
        self.delivery_station = (0,7)
        self.agents = []

    def add_agent(self, agent):
        """
        Adds an agent to the grid.
        
        :param agent: the agent to be added to the grid
        """
        self.agents.append(agent)

    def add_object(self, obj):
        """
        Adds an object to the grid.
        :param obj: the object to be added to the grid
        """
        self.objects.append(obj)

    def render(self):
        """
        Method to render the grid world. The grid is represented as a 2D list of strings, where each string represents a cell in the grid.
        This method is used for debugging purposes and to visualize the grid in a simple and light text format. 
        The grid is printed to the console, with different symbols representing walls, objects, delivery station and agents.
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
        
    def populate(self, agents_config, objects_config):
        """
        Function that populates the grid with agents and objects based on the provided configurations.
       
        :param grid: the grid to be populated
        :param agents_config: a list of tuples, where each tuple contains the id, x and y coordinates of an agent
        :param objects_config: a list of tuples, where each tuple contains the x and y coordinates of an object
        """
        for agent_id, x, y in agents_config:
            agent = Agent(agent_id)
            agent.set_position(x, y, self)
            self.add_agent(agent)
        
        for x, y in objects_config:
            obj = Object((x, y))
            self.add_object(obj)

    def plot_grid(self, fig = None, ax = None):
        """
        Plots the grid using patches for walls, station, objects, and agents.
        
        :param fig: the figure to plot on, if None a new figure will be created
        :param ax: the axes to plot on, if None new axes will be created
        """
        if fig is None or ax is None:
            fig, ax = plt.subplots(figsize = (8, 8))

        # Set axis limits and appearance
        ax.set_xlim(0, self.size )
        ax.set_ylim(self.size, 0)
        ax.set_aspect('equal')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
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

        :param id: the identifier of the agent, also used for rendering and/or plotting the grid
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
        :param picked: boolean attribute indicating the picked status of the object
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
    Centralized Trainer for Multi-Agent Q-learning. Manages a single joint Q-table for all agents.

    :param grid: the grid environment in which the agents operate
    :param c1: the initial learning rate multiplier
    :param c2: the learning rate decay factor
    :param alpha: the learning rate
    :param gamma: the discount factor for future rewards
    :param epsilon: the exploration rate for epsilon-greedy action selection
    :param num_states: the total number of joint states in the environment
    :param action_names: the list of possible actions for each agent
    :param num_joint_actions: the total number of joint actions
    :param q_table: the Q-table that stores the Q-values for each state-action pair. Dimension: 4096x64
    """
    def __init__(self, grid, c1=1, c2=1, gamma=0.9):
        
        self.grid = grid
        self.t = 0
        self.c1 = c1
        self.c2 = c2
        self.alpha = self.c1 / (self.c2 + self.t)
        self.gamma = gamma
        self.epsilon = 0.1
        self.num_states = (grid.size ** 2) ** len(grid.agents)
        self.action_names = list(DIRECTIONS.keys())
        self.num_joint_actions = len(self.action_names) ** len(grid.agents)
        self.q_table = np.zeros((self.num_states, self.num_joint_actions))

    def get_state_index(self):
        """
        Map joint agent positions to a single state index.

        :return: the index of the current state in the Q-table, computed based on the positions of all agents in the grid
        """
        idx = 0
        coords = []
        for agent in self.grid.agents:
            x, y = agent.position
            pos_idx = y * self.grid.size + x
            coords.append(pos_idx)

        idx = coords[0] + coords[1] * (self.grid.size ** 2)
        return idx
    
    def get_joint_action(self, action_idx):
        """
        Map joint action index back to individual agent actions.

        :param action_idx: the index of the joint action in the Q-table

        :return: a list of actions for each agent corresponding to the given joint action index
        """
        shape = (4, 4)
        indices = np.unravel_index(action_idx, shape=shape)
        joint_actions = []

        for i in indices:
            action_name = self.action_names[i]
            joint_actions.append(action_name)

        return joint_actions
    
    def manhattan_distance(self, p1, p2):
        """
        Return Manhattan distance between two grid positions.
        
        :param p1: the first position as a tuple (x, y)
        :param p2: the second position as a tuple (x, y)
        """

        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    def dynamic_reward(self, prev_pos, current_pos, unpicked_objects, all_collected):
        """
        Compute a small potential-based reward using Manhattan attraction.

        - While objects remain, only object potentials are active.
        - When all objects are collected, station potential is activated.
        - If an agent moves closer to the station before all objects are collected, apply a small penalty.

        :param prev_pos: the previous position of the agent
        :param current_pos: the current position of the agent
        :param unpicked_objects: list of objects that have not been picked yet
        :param all_collected: boolean indicating whether all objects have been collected
        """
        reward = 0.0

        if not all_collected and unpicked_objects:
            old_dist = min(self.manhattan_distance(prev_pos, obj.position) for obj in unpicked_objects)
            new_dist = min(self.manhattan_distance(current_pos, obj.position) for obj in unpicked_objects)
            reward += 0.05 * (old_dist - new_dist)

            # Penalize moving toward the station before all objects are collected
            old_station = self.manhattan_distance(prev_pos, self.grid.delivery_station)
            new_station = self.manhattan_distance(current_pos, self.grid.delivery_station)
            if new_station < old_station:
                reward -= 0.1

        elif all_collected:
            old_station = self.manhattan_distance(prev_pos, self.grid.delivery_station)
            new_station = self.manhattan_distance(current_pos, self.grid.delivery_station)
            reward += 0.05 * (old_station - new_station)

        return reward

    def select_action(self, state_idx):
            """
            Epsilon-greedy action selection.

            :param state_idx: the index of the current state in the Q-table

            :return: the index of the joint action selected based on epsilon-greedy strategy
            """
            if np.random.rand() < self.epsilon:
                action = np.random.randint(self.num_joint_actions)
                return action
            
            else:
                action = np.argmax(self.q_table[state_idx])
                return action

    def step(self, joint_action_idx):
        """
        Execute joint action, handle object collection, and check goal.

        :param joint_action_idx: the index of the joint action to be executed

        :return: a tuple containing the total reward obtained from executing the joint action and a boolean indicating whether the goal has been reached
        """
        actions = self.get_joint_action(joint_action_idx)
        total_reward = 0
        previous_positions = [agent.position for agent in self.grid.agents]
        outcome = []
        
        # Apply actions
        for i, agent in enumerate(self.grid.agents):
            outcome.append(agent.move(actions[i], self.grid))

        unpicked_objects = [obj for obj in self.grid.objects if not obj.picked]
        all_collected = len(unpicked_objects) == 0
        reached_goal = False

        for (agent,prev_pos), (success, attempted_position) in zip(zip(self.grid.agents, previous_positions), outcome):
            if not success: # wall or out of bounds
                total_reward -= 0.5
            else:
                is_picked = False # flag for a picked object
                for obj in self.grid.objects:
                    if not obj.picked and agent.position == obj.position:
                        obj.set_picked(True)
                        total_reward += 10 # Reward for one picked object 
                        is_picked = True
                        break
                if not is_picked:
                    total_reward -= 0.04

                # Add potential-based attraction reward
                total_reward += self.dynamic_reward(prev_pos, agent.position, unpicked_objects, all_collected)

        # Recompute object status after any pickups
        unpicked_objects = []
        for obj in self.grid.objects:
            if not obj.picked:
                unpicked_objects.append(obj)

        if len(unpicked_objects) == 0:
            all_collected = True
        else:
            all_collected = False

        if all_collected:

            all_on_station = all(agent.position == self.grid.delivery_station for agent in self.grid.agents)
            if all_on_station:
                total_reward += 50  # goal reward
                reached_goal = True

        return total_reward, reached_goal

    def update(self, state, action, reward, next_state):
            """
            Update the Q table using the Q-learning update rule.

            :param state: current state index before taking the action
            :param action: index of the joint action taken in the current state
            :param reward: reward obtained after taking the action
            :param next_state: index of the next state after taking the action
            """

            self.t += 1
            self.alpha = self.c1 / (self.c2 + self.t)

            best_next_action = np.argmax(self.q_table[next_state])
            estimated_q_opt = reward + self.gamma * self.q_table[next_state][best_next_action]

            # Q table update
            self.q_table[state][action] += self.alpha * (estimated_q_opt - self.q_table[state][action])

    def train(self, episodes, decay_rate):
            """
            Execute the training process for a specified number of episodes.

            :param episodes: the number of training episodes to execute
            :param decay_rate: the decay rate of epsilon
            """
            for ep in range(episodes):

                self.grid.reset_grid()
                

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

    def animate_grid(self, interval=100, repeat=True):
        """
        Function to animate the grid world using matplotlib's FuncAnimation.
        The generator frame_gen() counts the frames and stops when done=True.
        
        :param interval: time in milliseconds between frames
        :param repeat: whether the animation should repeat after completion
        """
        
        fig, ax = plt.subplots(figsize=(5, 5))
        self.grid.reset_grid()

        done = False

        def frame_gen():
            
            nonlocal done
            
            i = 0
            
            while not done:
                yield i
                i += 1

        def update(frame):
            
            nonlocal done
            
            ax.clear()
            # Show first frame with initial grid
            if frame == 0:
                self.grid.plot_grid(fig=fig, ax=ax)
                return []
            
            state = self.get_state_index()
            action = self.select_action(state)
            reward, done = self.step(action)
            self.grid.plot_grid(fig=fig, ax=ax)
            return []

        anim = FuncAnimation(fig=fig, func=update, frames=frame_gen(), interval=interval, repeat=repeat)
        return anim


if __name__ == "__main__":

# - - - HYPERPARAMETERS CONFIGURATION - - -
    
    HP_C1 = 1
    HP_C2 = 1
    HP_GAMMA = 0.9
    HP_EPISODES = 100
    HP_EPSILON = 0.33

    g = Grid(8)
    g.populate(AGENTS, OBJECTS)
    print('Initial grid:')
    
    trainer = Trainer(g, c1=HP_C1, c2=HP_C2, gamma=HP_GAMMA)
    
    # - - - TRAINING - - -

    # print(f"Hyperparameters: c1={HP_C1}, c2={HP_C2}, gamma={HP_GAMMA}")
    # print(f"Starting Centralized Training with c1={trainer.c1}, c2={trainer.c2}, gamma={trainer.gamma}...")
    # trainer.train(episodes = HP_EPISODES, decay_rate=0.99)

    # - - - Q-TABLE SAVE - - -

    # np.save(f'std_episodes_{HP_EPISODES}_eps_{HP_EPSILON}.npy', trainer.q_table)
    # print("Q-table salvata")
    
    # - - - Q-TABLE LOAD - - -

    trainer.q_table = np.load(f'std_episodes_{HP_EPISODES}_eps_{HP_EPSILON}.npy')   

    # - - - ANIMAZIONE - - - RICORDA PASSARE MAX_STEPS PER DECIDERE LUNGHEZZA

    g.reset_grid()
    anim = trainer.animate_grid()
    
    # - - - GIF SAVE - - -

    #anim.save('Q_learning_grid.gif', writer=PillowWriter(fps=2, bitrate=1000), dpi=100)

    # - - - MP4 SAVE - - -
    
    anim.save(f'std_episodes_{HP_EPISODES}_eps_{HP_EPSILON}.mp4', writer=FFMpegWriter(fps=5, bitrate=1000), dpi=100)

    
    # - - - DEMO TEST - - -

    # g.reset_grid()

    # done = False
    # steps = 0
    # print("Starting demo ...")
    # while not done and steps < 100000:
    #     state = trainer.get_state_index()
    #     action = trainer.select_action(state)
    #     reward, done = trainer.step(action)
    #     steps += 1
    #     g.render()
    #     print(f"Epsilon finale: {trainer.epsilon:.16f}")
    #     print(f"State: {state}")
    #     print(f"Steps: {steps}")
    #     time.sleep(0.15)
    
    # if done:
    #     print(f"Goal Reached in {steps} steps!")
    # else:
    #     print("Demo completed without reaching the goal.")
    
