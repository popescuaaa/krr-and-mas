
# coding: utf-8

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from itertools import product


# ## The problem: *The Climber Robot*
# Grid Representation

COLORS = ["Black", "Red", "Green", "Blue", "Orange"]

class Grid(object): 
    def __init__(self, name, elevation, color, p_t=.8, p_o=.8):
        self._name = name
        self.elevation = np.array(elevation)
        self.color = np.array(color)
        assert self.elevation.shape == self.color.shape
        self.p_t = p_t
        self.p_o = p_o
        
    @property
    def name(self):
        return self._name
    
    @property
    def states_no(self):
        return self.elevation.size
    
    @property
    def shape(self):
        return self.elevation.shape
    
    def get_neighbours(self, state):
        """Returns a list of tuples (neighbour, probability)"""
        y, x = state
        H, W = self.shape

        neighbours = []
        for (dy, dx) in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            ny, nx = y + dy, x + dx
            if ny >= 0 and nx >=0 and ny < H and nx < W:
                neighbours.append((ny, nx))

        elevation = [self.elevation[i] for i in neighbours]
        max_e = max(elevation)
        max_no = len([e for e in elevation if e == max_e])
        p_other = (1. - self.p_t) / len(neighbours)
        p_max = (self.p_t / max_no) + p_other
        prob = [p_max if e == max_e else p_other for e in elevation]

        return list(zip(neighbours, prob))
    
    def get_colors(self, state):
        """Returns a list of tuples (color, probability)"""
        y, x = state
        p_other = (1. - self.p_o) / len(COLORS)
        p_real = self.p_o + p_other
        rc = self.color[y, x]
        return [(i, p_real if i == rc else p_other) for (i, c) in enumerate(COLORS)]

    def get_liniarized_states(self):
        states = []
        H, W = self.shape
        for y in range(H):
            for x in range(W):
                states.append((y, x))

        return states


# ### Three toy grids to play with
# We'll use the following three grids to test our algorithms.

grid = Grid("Grid 1",
             [[4, 5, 6], [2, 3, 7], [1, 2, 8]],  # elevation
             [[0, 1, 2], [0, 0, 3], [0, 0, 4]])  # color


fig, ax = plt.subplots(1, 1, figsize=(5 * 1, 4), sharey="row")
cm = LinearSegmentedColormap.from_list("cm", COLORS)
sns.heatmap(grid.color, annot=grid.elevation, cmap=cm,
            square=True, cbar=False, annot_kws={"size": 30}, ax=ax)
ax.set_title(grid.name)


# ================== Extracting the HMM parameters ==================
# 
# Given a `Grid` object, build the three matrices of parameters Pi, A, B. The results should be `numpy` arrays.

# ### Initial state distribution
def get_initial_distribution(grid):
    N = grid.states_no
    d = np.zeros(N)
    d[0] = 1.0
    return d
    

# ### Transition probability matrix
def get_transition_probabilities(grid):
    H, W = grid.shape
    N = H * W
    A = np.zeros((N, N))
    
    for x in range(H):
        for y in range(W):
            for n_st, prob in grid.get_neighbours((x, y)):
                xx,yy = n_st
                A[x * W + y][xx * W + yy] = prob

    return A



# Visualize transition probabilities matrices

fig, ax = plt.subplots(1, 1, figsize=(6 * 1, 4), sharey="row")
A = get_transition_probabilities(grid)
sns.heatmap(A, square=True, cbar=True, ax=ax, cmap="Blues")
ax.set_title(grid.name)


# ### Emission probability matrix
def get_emission_probabilities(grid):
    H, W = grid.shape
    N = grid.states_no
    B = np.zeros((H * W, len(COLORS)))
    
    for x in range(H) :
        for y in range(W) :
            for color, prob in grid.get_colors((x,y)):
                B[x * W + y][color] = prob       
    
    return B

# Visualize emission probabilities
fig, ax = plt.subplots(1, 1, figsize=(1 * 4, 6), sharey="row")
N = grid.states_no
_colors = np.array([list(range(len(COLORS))) for _ in range(N)])
B = get_emission_probabilities(grid)
cm = LinearSegmentedColormap.from_list("cm", COLORS)
sns.heatmap(_colors, cmap=cm, annot=B, ax=ax)
ax.set_title(grid.name)


# ## Sampling from the model
# 
# Given a model (a `Grid`) function `get_sequence` returns a sequence of observations and the corresponding states.
def sample(probabilities):
    s, t = .0, np.random.sample()
    for (value, p) in probabilities:
        s += p
        if s >= t:
            return value
    raise ValueError("Probabilities " + str(probabilities) + " do not sum to one!")


def get_sequence(grid, length):
    H, W = grid.shape

    states, observations = [], []
    for t in range(length):
        if t == 0:
            all_states = grid.get_liniarized_states()
            state_idx = np.random.choice(np.arange(grid.states_no), p=np.array(get_initial_distribution(grid)))
            state = all_states[state_idx]
        else:
            state = sample(grid.get_neighbours(state))
        o = sample(grid.get_colors(state))
        states.append(state)
        observations.append(o)
        
    return observations, states


# Generate a dataset of observation sequences to learn from
T = 5
NUM_SEQUENCES = 100
dataset = []

for idx in range(NUM_SEQUENCES):
    observations, states = get_sequence(grid, T)
    dataset.append(observations)

# ====================== Learning =======================
# 
# We'll now apply the Baum-Welch algorithm to estimate the A and B matrices.
# pi is already known, so we do not need to estimate it
# We use the above generated dataset.


# ### Compute Forward-Backward values
# Compute the probability that a given sequence comes from a given model

def forward_backward(grid, observations):
    # TODO 1: Compute p, alpha and beta values
    N = grid.states_no
    T = len(observations)
    alpha = np.zeros((T, N))
    beta = np.zeros((T, N))
    
    pi = get_initial_distribution(grid)
    A = get_transition_probabilities(grid)
    B = get_emission_probabilities(grid)
    

    # TODO 3 ends here

    p = sum(alpha[-1,])
    return p, alpha, beta


def baum_welch(dataset, eps = 1e-2):
    N = grid.states_no
    T = len(dataset[0])
    
    # pi is already known
    pi = get_initial_distribution(grid)
    
    # initialize A and B to be probability matrices
    A = np.random.random((N, N))
    for i in range(N):
        A[i, :] /= np.sum(A[i])
    
    B = np.random.random((N, len(COLORS)))
    for i in range(N):
        B[i, :] /= np.sum(B[i])
        
        
    # ### TODO 2: implement baum welch
    
    # ### End TODO 2
    return pi, A, B

_, A_estimated, B_estimated = baum_welch(dataset)

# Visualize estimated transition probability matrices
fig, ax = plt.subplots(1, 1, figsize=(6 * 1, 4), sharey="row")
sns.heatmap(A_estimated, square=True, cbar=True, ax=ax, cmap="Blues")
ax.set_title("Estimated Transition Matrix")

# Visualize emission probabilities
fig, ax = plt.subplots(1, 1, figsize=(1 * 4, 6), sharey="row")
N = grid.states_no
_colors = np.array([list(range(len(COLORS))) for _ in range(N)])
cm = LinearSegmentedColormap.from_list("cm", COLORS)
sns.heatmap(_colors, cmap=cm, annot=B_estimated, ax=ax)
ax.set_title("Estimated Emission Matrix")