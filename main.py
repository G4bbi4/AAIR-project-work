import matplotlib.pyplot as plt
import matplotlib.artist
from matplotlib.text import Text
from matplotlib import animation
import numpy as np
from enum import Enum

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
            raise ValueError("Cannot set position on a wall.") #probabilmente da modificare perché si vuole che l'agente resti fermo se si prova a muoverlo in una posizione non valida, invece di sollevare un'eccezione
        else:
            self.position = (x, y)

    def move(self, direction):
        """
        Moves the agent in the specified direction if the new position is valid.
        :param direction: the direction where the agent should move (up, down, left, right)
        """
        if direction not in DIRECTIONS:
            raise ValueError(f"Direzione sconosciuta: {direction}")
        
        dx, dy = DIRECTIONS[direction]
        x, y = self.position
        self.set_position(x + dx, y + dy)

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
    # g.agents[0].move("down")
    # print('Grid after moving agent down:')
    # g.render()