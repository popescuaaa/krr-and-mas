
# coding: utf-8

# # Hidden Markov Models
# 
#     Tudor Berariu (tudor.berariu@gmail.com), 2018
     

# Let's import some packages for later

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from itertools import product


# ## The problem: *The Climber Robot*
# Grid Representation


COLORS = ["Black", "Red", "Green", "Blue"]

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


# ### Three toy grids to play with
# We'll use the following three grids to test our algorithms.

grid1 = Grid("Grid 1",
             [[1, 2, 3, 5], [2, 2, 1, 2], [3, 2, 1, 1], [0, 0, 0, 0]],  # elevation
             [[0, 3, 1, 2], [3, 1, 2, 0], [2, 2, 0, 0], [3, 0, 3, 1]])  # color

grid2 = Grid("Grid 2",
             [[0, 0, 1, 1], [2, 1, 0, 2], [1, 0, 0, 2], [4, 4, 3, 3]],  # elevation
             [[0, 3, 1, 2], [3, 1, 2, 0], [2, 2, 0, 0], [3, 0, 3, 1]])  # color

grid3 = Grid("Grid 3",
             [[2, 1, 2, 3], [1, 1, 2, 2], [1, 0, 1, 1], [2, 1, 1, 2]],  # elevation
             [[2, 3, 1, 0], [1, 3, 3, 1], [0, 2, 0, 2], [2, 1, 1, 2]])  # color

GRIDS = [grid1, grid2, grid3]


_g_no = len(GRIDS)
fig, axs = plt.subplots(1, _g_no, figsize=(5 * _g_no, 4), sharey="row")
for grid, ax in zip(GRIDS, axs):
    cm = LinearSegmentedColormap.from_list("cm", COLORS)
    sns.heatmap(grid.color, annot=grid.elevation, cmap=cm,
                square=True, cbar=False, annot_kws={"size": 30}, ax=ax)
    ax.set_title(grid.name)


# ================== Extracting the HMM parameters ==================
# 
# Given a `Grid` object, build the three matrices of parameters Pi, A, B. The results should be `numpy` arrays.
# 
#  - Task 1: implement function `get_transition_probabilities`
#  - Task 2: implement function `get_emission_probabilities`

# ### Initial state distribution
def get_initial_distribution(grid):
    N = grid.states_no
    return np.ones(N) / N


# ### Transition probability matrix
def get_transition_probabilities(grid):
    H, W = grid.shape
    N = H * W
    A = np.zeros((N, N))
    
    # TODO *1*: Complete the transition probablities matrix A.
    # Hint: Use the `get_neighbours` method.
    
    # TODO *1* ends here

    return A



# Visualize transition probabilities matrices
_g_no = len(GRIDS)
fig, axs = plt.subplots(1, _g_no, figsize=(6 * _g_no, 4), sharey="row")
for grid, ax in zip(GRIDS, axs):
    A = get_transition_probabilities(grid)
    sns.heatmap(A, square=True, cbar=True, ax=ax, cmap="Blues")
    ax.set_title(grid.name)


# Test transition probabilities

_test_idxs = [0, 1, 2, 5, 10, 13, 15], [1, 0, 3, 4, 9, 2, 14]
_test_values = np.array([
    [.5,      .2 / 3, .8 + .2 / 3, .8 / 3 + .05, .85, 0, .1],
    [.1,      .2 / 3, .8 + .2 / 3,          .85, .05, 0, .9],
    [.5, .4 + .2 / 3, .8 + .2 / 3,          .05, .05, 0, .5]
])

for i, grid in enumerate(GRIDS):
    A = get_transition_probabilities(grid)
    assert A.shape == (grid.states_no, grid.states_no), "Bad shape!"
    assert np.allclose(A.sum(axis=1), np.ones(grid.states_no)), "Rows should sum to one!"
    assert np.allclose(A[_test_idxs], _test_values[i]), "Bad values!"
    
print("Transition matrix looks right! Task 1 accomplished!")


# ### Emission probability matrix
def get_emission_probabilities(grid):
    H, W = grid.shape
    N = grid.states_no
    B = np.zeros((H * W, len(COLORS)))
    
    # Task 2: Compute the emission probabilities matrix.
    # Hint: Use method `get_colors`.

    # Task 2 ends here.        
    
    return B

# Visualize emission probabilities

_g_no = len(GRIDS)
fig, axs = plt.subplots(1, _g_no, figsize=(_g_no * 4, 6), sharey="row")

for grid, ax in zip(GRIDS, axs):
    N = grid.states_no
    _colors = np.array([list(range(len(COLORS))) for _ in range(N)])
    B = get_emission_probabilities(grid)
    cm = LinearSegmentedColormap.from_list("cm", COLORS)
    sns.heatmap(_colors, cmap=cm, annot=B, ax=ax)
    ax.set_title(grid.name)


#### Test emission probabilitiees

_test_idxs = [0, 3, 2, 5, 10, 13, 15], [2, 2, 3, 0, 1, 1, 1]
_test_values = np.array([
    [.05, .85, .05, .05, .05, .05, .85],
    [.05, .85, .05, .05, .05, .05, .85],
    [.85, .05, .05, .05, .05, .85, .05]
])

for i, grid in enumerate(GRIDS):
    B = get_emission_probabilities(grid)
    assert B.shape == (grid.states_no, len(COLORS)), "Bad shape!"
    assert np.allclose(B.sum(axis=1), np.ones(grid.states_no)), "Rows should sum to one!"
    assert np.allclose(B[_test_idxs], _test_values[i]), "Bad values for " + grid.name + "!"
    
print("Emission probabilities look right! Task 2 accomplished!")


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
            state = np.random.randint(H), np.random.randint(W)
        else:
            state = sample(grid.get_neighbours(state))
        o = sample(grid.get_colors(state))
        states.append(state)
        observations.append(o)
        
    return observations, states


# Example of a random sequence from a random model
grid = np.random.choice(GRIDS)
T = np.random.randint(2, 6)
observations, states = get_sequence(grid, T)

print("Agent wandered on map \033[1m" + grid.name + "\033[0m")
print("... going thorugh states", states)
print("... observing", ", ".join([COLORS[o] for o in observations]))

cm = LinearSegmentedColormap.from_list("cm", COLORS)
ax = sns.heatmap(grid.color, annot=grid.elevation, cmap=cm,
                 square=True, cbar=False, annot_kws={"size": 20})
ax.set_title(grid.name)
for t in range(T-1):
    y0, x0 = states[t]
    y0, x0 = y0 + .5, x0 + .5
    y1, x1 = states[t + 1]
    y1, x1 = y1 + .5, x1 + .5
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(color="y", width=5.))


# ====================== Evaluation =======================
# 
# We'll now evaluate the probabiity that a given sequence of observations was generated by a given model.
# We will look at a sequence and see if we can figure out which grid generated it.


# ### Compute Forward values
# Compute the probability that a given sequence comes from a given model

def forward(grid, observations):
    # TODO 3: Compute p and alpha values
    N = grid.states_no
    T = len(observations)
    alpha = np.zeros((T, N))
    
    # TODO 3: Compute p and alpha values.
    # Hint: use the functions implemented for the previous tasks.
    pi = get_initial_distribution(grid)
    A = get_transition_probabilities(grid)
    B = get_emission_probabilities(grid)
    

    # TODO 3 ends here

    p = sum(alpha[-1,])
    return p, alpha

# See the forward algorithm in action
grid = np.random.choice(GRIDS)
print("The real model is \033[1m" + grid.name + "\033[0m")

T = np.random.randint(2, 10)
observations, _ = get_sequence(grid, T)
print("The observed sequence is", ", ".join([COLORS[i] for i in observations]))

best_grid, best_p = None, None
for grid in GRIDS:
    p, _ = forward(grid, observations)
    print("Probability that comes from " + grid.name + " is %f." % (p))
    if best_grid is None or best_p < p:
        best_grid, best_p = grid.name, p

print("Most probably the sequence was generated from " + best_grid + ".")


# See how sequence length influences p
RUNS_NO = 1000

for T in range(1, 11):
    correct = 0
    for _ in range(RUNS_NO):
        true_grid = np.random.choice(GRIDS)
        observations, _ = get_sequence(true_grid, T)
        best_grid, best_p = None, None
        for grid in GRIDS:
            p, _ = forward(grid, observations)
            if best_grid is None or best_p < p:
                best_grid, best_p = grid.name, p
        correct += (best_grid == true_grid.name)
    perc = float(correct * 100) / RUNS_NO
    print("%5d / %d (%5.2f%%) for T = %2d" % (correct, RUNS_NO, perc, T))

# Test alpha_values
_test_observations = [2, 2, 3]
_test_values = np.array([
 [  3.12500000e-03, 3.12500000e-03, 3.12500000e-03, 5.31250000e-02,
    3.12500000e-03, 3.12500000e-03, 5.31250000e-02, 3.12500000e-03,
    5.31250000e-02, 5.31250000e-02, 3.12500000e-03, 3.12500000e-03,
    3.12500000e-03, 3.12500000e-03, 3.12500000e-03, 3.12500000e-03],
 [  2.08333333e-05, 1.38020833e-04, 4.78385417e-03, 4.60416667e-03,
    1.36718750e-03, 2.86458333e-04, 6.19791667e-04, 5.33854167e-04,
    4.30755208e-02, 2.64739583e-02, 4.11458333e-04, 1.58854167e-04,
    1.87500000e-04, 1.58854167e-04, 3.38541667e-05, 2.08333333e-05],
 [  5.01736111e-06, 3.57044271e-04, 2.39509549e-04, 2.30434028e-04,
    1.71725825e-02, 7.27517361e-05, 1.94704861e-05, 3.14539931e-05,
    1.19282552e-03, 1.03400174e-03, 6.97309028e-05, 3.74565972e-06,
    2.44994792e-03, 6.72352431e-05, 2.82595486e-05, 6.42361111e-07]])

p, alpha = forward(grid1, [2, 2, 3])
assert alpha.shape == (3, grid1.states_no), "Bad shape!"
assert np.allclose(alpha, _test_values), "Bad values!"
assert np.allclose(p, sum(_test_values[2])), "Bad values!"
    
print("Alpha matrix looks right! Task 3 accomplished!")


# ## Decoding
# For decoding we'll use the Viterbi algorithm.
def viterbi(grid, observations):
    N = grid.states_no
    H, W = grid.shape
    T = len(observations)
    delta = np.zeros((T, N))
    states = np.zeros((T), dtype=int)
    
    # Task 4: Implement the Viterbi algorithm.
    # Hint: use functions from tasks 1 and 2.
    pi = get_initial_distribution(grid)
    A = get_transition_probabilities(grid)
    B = get_emission_probabilities(grid)
    # 
    
    # Task 4 ends here.

    return [(s // W, s % W) for s in states], delta

# Decoding a state
grid = np.random.choice(GRIDS)
T = np.random.randint(3, 6)
observations, states = get_sequence(grid, T)
decoded, _ = viterbi(grid, observations)

print("Agent wandered on map \033[1m" + grid.name + "\033[0m")
print("... going thorugh states", states)
print("... observing", ", ".join([COLORS[o] for o in observations]))
print("\nThe decoded sequence of states is", decoded)

fig, axs = plt.subplots(1, 2, figsize=(10, 4), sharey="row")
cm = LinearSegmentedColormap.from_list("cm", COLORS)
sns.heatmap(grid.color, annot=grid.elevation, cmap=cm, square=True,
            cbar=False, annot_kws={"size": 20}, ax=axs[0])
sns.heatmap(grid.color, annot=grid.elevation, cmap=cm, square=True,
            cbar=False, annot_kws={"size": 20}, ax=axs[1])
axs[0].set_title(grid.name + " - original path")
axs[1].set_title(grid.name + " - decoded path")

for t in range(T - 1):
    (y0, x0), (y1, x1) = states[t], states[t + 1]
    y0, x0, y1, x1 = y0 + .5, x0 + .5, y1 + .5, x1 + .5
    axs[0].annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(color="y", width=5.))
    (y0, x0), (y1, x1) = decoded[t], decoded[t + 1]
    y0, x0, y1, x1 = y0 + .5, x0 + .5, y1 + .5, x1 + .5
    axs[1].annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(color="y", width=5.))


# Evaluate how good the decoded paths are
RUNS_NO = 1000
print("Number of states correctly decoded.")
for T in range(1, 11):
    correct = 0
    for run_id in range(RUNS_NO):
        grid = np.random.choice(GRIDS)
        observations, states = get_sequence(grid, T)
        decoded, _ = viterbi(grid, observations)
        correct += sum([a == b for a, b in zip(states, decoded)])
    perc = float(correct * 100) / (RUNS_NO * T)
    print("%5d / %5d (%5.2f%%) for T =%2d" % (correct, RUNS_NO * T, perc, T))

# Testing Viterbi

_test_states = [(1, 3), (2, 3), (3, 3), (3, 2)]
_test_values = [[5.31250000e-02, 3.12500000e-03, 3.12500000e-03, 3.12500000e-03,
                 3.12500000e-03, 3.12500000e-03, 3.12500000e-03, 5.31250000e-02,
                 3.12500000e-03, 3.12500000e-03, 5.31250000e-02, 5.31250000e-02,
                 3.12500000e-03, 5.31250000e-02, 3.12500000e-03, 3.12500000e-03],
                [1.77083333e-04, 2.65625000e-04, 7.29166667e-05, 1.77083333e-04,
                 2.39062500e-03, 7.29166667e-05, 1.77083333e-04, 3.01041667e-03,
                 7.29166667e-05, 1.77083333e-04, 3.01041667e-03, 3.91354167e-02,
                 2.30208333e-03, 2.39062500e-03, 2.25781250e-03, 2.30208333e-03],
                [7.96875000e-06, 8.85416667e-07, 1.05364583e-04, 1.00347222e-05,
                 7.96875000e-06, 9.48281250e-04, 1.00347222e-05, 1.30451389e-04,
                 5.57812500e-05, 7.96875000e-06, 1.30451389e-04, 1.30451389e-04,
                 1.03593750e-04, 1.03593750e-04, 1.27942708e-04, 2.88297569e-02],
                [2.65625000e-08, 4.03019531e-05, 5.01736111e-08, 4.56579861e-06,
                 6.85133203e-04, 1.85937500e-07, 2.37070312e-06, 4.51562500e-07,
                 5.17968750e-07, 2.37070312e-06, 4.34837963e-07, 1.44148785e-04,
                 7.63140625e-05, 5.54418403e-06, 2.20547641e-02, 5.65289352e-06]]
states, delta = viterbi(grid2, [0, 0, 1, 3])
assert len(states) == len(_test_states)
assert all([s_i == s_j for (s_i, s_j) in zip(states, _test_states)])
assert np.allclose(delta, _test_values)

print("Viterbi looks right! Task 4 accomplished!")

