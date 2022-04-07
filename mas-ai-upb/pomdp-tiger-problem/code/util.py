import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
from typing import Dict, Tuple
from env import *


def display(policies: Dict, ncols: int = 3):
    """
    Parameters
    ----------
    policies
        Full dictionary of policies
    ncol
        Number of plots per row(columns)
    """

    num_steps = len(policies)
    nrows = num_steps // ncols + (num_steps % ncols != 0)

    fig, ax = plt.subplots(nrows, ncols, figsize=(20, 10))
    for i in policies:
        # print("Policy index: ", i)

        row, col = i // ncols, i % ncols
        # extract x1, y1 components
        x1 = [b[0] for b in policies[i]["policy"]]
        y1 = policies[i]["scores"]

        # print("Nr policies: ", len(policies))
        g = ax[row][col] if len(policies) > ncols else ax[col]
        # plot scores
        g.stem(x1, y1, 'o--', basefmt="b")
        g.set_title(f"Value Function Step {i}")

        for v in policies[i]["V"]:
            col1 = np.linspace(1, 0, 1000).reshape(-1, 1)
            col2 = 1 - col1
            matrix = np.concatenate([col1, col2], axis=1)

            # compute points then filter
            y2 = np.dot(matrix, v)
            idx = (np.min(y1) <= y2) & (y2 <= np.max(y1))
            g.plot(col2[idx], y2[idx], )


def get_closest_belief(policy: Dict[Tuple, Actions], b) -> Tuple:
    keys = list(np.array(x) for x in policy.keys())
    dist = [np.linalg.norm(b - x) for x in keys]
    return keys[np.argmin(dist)]