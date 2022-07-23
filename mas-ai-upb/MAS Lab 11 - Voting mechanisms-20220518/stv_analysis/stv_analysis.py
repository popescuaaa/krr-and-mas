import math

from preflibtools import io
from preflibtools.generate_profiles import gen_mallows, gen_cand_map, gen_impartial_culture_strict
from typing import List, Dict, Tuple
import random
import matplotlib.pyplot as plt

PHIS = [0.7, 0.8, 0.9, 1.0]
NUM_VOTERS = [100, 500, 1000]
NUM_CANDIDATES = [3, 6, 10, 15]


def generate_random_mixture(nvoters: int = 100, ncandidates: int = 6, num_refs: int = 3, phi: float = 1.0) \
        -> Tuple[Dict[int, str], List[Dict[int, int]], List[int]]:
    """
    Function that will generate a `voting profile` where there are num_refs mixtures of a
    Mallows model, each with the same phi hyperparameter
    :param nvoters: number of voters
    :param ncandidates: number of candidates
    :param num_refs: number of Mallows Mixtures in the voting profile
    :param phi: hyper-parameter for each individual Mallows model
    :return: a tuple consisting of:
        the candidate map (map from candidate id to candidate name),
        a ranking list (list consisting of dictionaries that map from candidate id to order of preference)
        a ranking count (the number of times each vote order comes up in the ranking list,
        i.e. one or more voters may end up having the same preference over candidates)
    """
    candidate_map = gen_cand_map(ncandidates)

    mix = []
    phis = []
    refs = []

    for i in range(num_refs):
        refm, refc = gen_impartial_culture_strict(1, candidate_map)
        refs.append(io.rankmap_to_order(refm[0]))
        phis.append(phi)
        mix.append(random.randint(1, 100))

    smix = sum(mix)
    mix = [float(m) / float(smix) for m in mix]

    rmaps, rmapscounts = gen_mallows(nvoters, candidate_map, mix, phis, refs)

    return candidate_map, rmaps, rmapscounts


def simple_stv(nvoters: int,
               canidate_map: Dict[int, str],
               rankings: List[Dict[int, int]],
               ranking_counts: List,
               top_k: int,
               is_stv_k: bool,
               required_elected: int) -> List[int]:
    quota = math.floor((nvoters / len(rankings) + 1) + 1)
    print(quota)

    c_places = {}
    for c_idx in canidate_map:
        c_places[c_idx] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

    for ranking in rankings:
        for c_idx in ranking:
            c_places[c_idx][ranking[c_idx]] += 1

    if is_stv_k:
        items = c_places.items()
        c_places = sorted(items, key=lambda e: e[1][1], reverse=True)
        c_places = c_places[:top_k]
        c_places = {k: v for k, v in c_places}

    print(c_places)

    winners = []
    print(quota)

    while len(winners) < required_elected:
        if len(c_places) == 0:
            break

        winner = None
        for candidate in c_places:
            if c_places[candidate][1] >= quota:
                winners.append(candidate)
                winner = candidate
                break

        print("Current winner", winner)
        if winner is not None:
            # Redistribute votes
            if c_places[winner][1] >= quota:
                diff = c_places[winner][1] - quota
                # Move votes to next candidates and eliminate this one
                del c_places[winner]
                # Sort the rest
                items = c_places.items()
                c_places = sorted(items, key=lambda e: e[1][1], reverse=True)
                # Candidates
                if len(c_places) > 1:
                    c_places[0][1][1] += diff // 2
                    c_places[1][1][1] += diff // 2
                else:
                    if len(c_places) == 0:
                        break
                    else:
                        c_places[0][1][1] += diff

                c_places = {k: v for k, v in c_places}
        else:
            items = c_places.items()
            c_places = sorted(items, key=lambda e: e[1][1], reverse=True)

            # Drop the last one
            last_one = c_places[-1][0]
            last_one_votes = c_places[-1][1][1]
            portion = last_one_votes // len(c_places)
            # Everybody gets votes from this one
            for e in c_places:
                if e[0] != last_one:
                    e[1][1] += portion

            c_places = {k: v for k, v in c_places}
            del c_places[last_one]

    if not is_stv_k:
        print("The winners after classical stv are:", winners)
    else:
        print("The winners after k stv are:", winners)

    return winners


def stv(nvoters: int,
        canidate_map: Dict[int, str],
        rankings: List[Dict[int, int]],
        ranking_counts: List,
        top_k: int,
        required_elected: int) -> int:
    # Simple stv
    stv_winners = simple_stv(nvoters=nvoters, canidate_map=canidate_map, rankings=rankings,
                             ranking_counts=ranking_counts, required_elected=required_elected, is_stv_k=False,
                             top_k=top_k)

    # Compute stv-k winners
    # Get the top k in the
    stv_k = simple_stv(nvoters=nvoters, canidate_map=canidate_map, rankings=rankings,
                       ranking_counts=ranking_counts, required_elected=required_elected, is_stv_k=True,
                       top_k=top_k)
    # Overlapping
    o = []
    for i in range(min(len(stv_k), len(stv_winners))):
        if stv_k[i] == stv_winners[i]:
            o.append(1)
        else:
            o.append(0)

    od = sum(o)

    print("Overlapping degree: {}".format(od))

    return od


if __name__ == "__main__":
    ods = []

    # cmap, rmaps, rmapscounts = generate_random_mixture()
    # od = stv(nvoters=100, canidate_map=cmap, rankings=rmaps, top_k=5, ranking_counts=rmapscounts, required_elected=3)
    # print(od)

    for phi in PHIS:
        ods = []
        for k in range(6):
            cmap, rmaps, rmapscounts = generate_random_mixture(phi=phi)
            od = stv(nvoters=100, canidate_map=cmap, rankings=rmaps, top_k=k, ranking_counts=rmapscounts,
                     required_elected=3)
            ods.append((phi, k, od))

            phis = list(map(lambda e: e[0], ods))
            k = list(map(lambda e: e[1], ods))
            ds = list(map(lambda e: e[2], ods))

            plt.plot(k, ds)

    plt.show()

    """
    bar: k, ds     
    """

