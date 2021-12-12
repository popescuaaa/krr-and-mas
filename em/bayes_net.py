from typing import List, Dict, Tuple, Any
import pandas as pd
import networkx as nx
import itertools
import random
from copy import deepcopy
import numpy as np


def almost_equal(x: float, y: float, threshold: float = 1e-6) -> bool:
    return abs(x-y) < threshold


def factor_crossjoin(f1: pd.DataFrame, f2: pd.DataFrame, how: str = "outer", **kwargs) -> pd.DataFrame:
    """
        Make a cross join (cartesian product) between two dataframes by using a constant temporary key.
        Also sets a MultiIndex which is the cartesian product of the indices of the input dataframes.
        See: https://github.com/pydata/pandas/issues/5401
        :param f1 first factor represented as a pandas DataFrame
        :param f2 second factor represented as a pandas DataFrame
        :param how type of the join to perform on factors - for the crossjoin the default is "outer"
        :param kwargs keyword arguments that will be passed to pd.merge()
        :return cross join of f1 and f2
        """
    f1['_tmpkey'] = 1
    f2['_tmpkey'] = 1

    res = pd.merge(f1.reset_index(), f2.reset_index(), on='_tmpkey', how=how, **kwargs).drop('_tmpkey', axis=1)
    res = res.set_index(keys=f1.index.names + f2.index.names)

    f1.drop('_tmpkey', axis=1, inplace=True)
    f2.drop('_tmpkey', axis=1, inplace=True)

    return res


def multiply_factors(f1: pd.DataFrame, f2: pd.DataFrame) -> pd.DataFrame:
    f1_vars = f1.index.names
    f2_vars = f2.index.names

    common_vars = [v for v in f1_vars if v in f2_vars]

    if not common_vars:
        ### we have to do a cross join
        f_res = BayesNode.factor_crossjoin(f1, f2)
        f_res["prob"] = f_res["prob_x"] * f_res["prob_y"]
        f_res = f_res.drop(columns=["prob_x", "prob_y"])

    else:
        ### there is a set of common vars, so we merge on them
        disjoint_vars = [v for v in f1_vars if v not in f2_vars] + [v for v in f2_vars if v not in f1_vars]
        f_res = pd.merge(f1.reset_index(), f2.reset_index(), on=common_vars, how="inner")\
            .set_index(keys=disjoint_vars + common_vars)
        f_res["prob"] = f_res["prob_x"] * f_res["prob_y"]
        f_res = f_res.drop(columns=["prob_x", "prob_y"])

    return f_res


def sumout(f:pd.DataFrame, vars: List[str]) -> pd.DataFrame or float:
    f_vars = f.index.names
    remaining_vars = [v for v in f_vars if v not in vars]

    if remaining_vars:
        return f.groupby(level=remaining_vars).sum()
    else:
        # if we are summing out all values return the sum of all entries
        return f["prob"].sum()


def normalize(f:pd.DataFrame) -> pd.DataFrame:
    f["prob"] = f["prob"] / f["prob"].sum()
    return f


class Factor:
    """
    Place holder class for a Factor in a factor graph (implicitly also within a junction tree)
    """
    def __init__(self, vars: List[str], table: pd.DataFrame):
        """
        Instantiate a factor
        :param vars: random variables of a factor
        :param table: factor table that is proportional to probabilities
        """
        self.vars = vars
        self.table = table



class BayesNode:
    def __init__(self,
                 var_name: str = None,
                 parent_nodes: List["BayesNode"] = None,
                 cpd: pd.DataFrame = None):
        """
        Defines a binary random variable in a bayesian network by
        :param var_name: the random variable name
        :param parent_nodes: the parent random variables (conditioning variables)
        :param cpd: the conditional probability distribution given in the form of a Pandas Dataframe which has a
        multilevel index that contains all possible binary value combinations for the random variable and its parents

        An example CPD is:
                   prob
            c a b
            1 1 1  0.946003
                0  0.080770
              0 1  0.664979
                0  0.223632
            0 1 1  0.751246
                0  0.355359
              0 1  0.688208
                0  0.994031

        The first level of the index is always the `var_name` random variable (the one for the current node)
        The next levels in the index correspond to the parent random variables
        """
        self.var_name = var_name
        self.parent_nodes = parent_nodes
        self.cpd = cpd

    def to_factor(self) -> Factor:
        factor_vars = [self.var_name] + [p.var_name for p in self.parent_nodes]
        return Factor(vars=factor_vars, table=self.cpd.copy(deep=True))

    def pretty_print(self):
        res = ""
        res += "Node(%s" % self.var_name
        if self.parent_nodes:
            res += " | "
            for p in [p.var_name for p in self.parent_nodes]:
                res += p + " "
            res += ")"
        else:
            res += ")"

        res += "\n"
        res += str(self.cpd)
        res += "\n"

        return res

    def __str__(self):
        res = ""
        res += "Node(%s" % self.var_name
        if self.parent_nodes:
            res += " | "
            for p in [p.var_name for p in self.parent_nodes]:
                res += p + " "
            res += ")"
        else:
            res += ")"

        return res

    def __repr__(self):
        return self.__str__()


class BayesNet:
    """
    Representation for a Bayesian Network
    """
    def __init__(self, bn_file: str="data/bnet"):
        # nodes are indexed by their variable name
        self.nodes, self.queries = BayesNet.parse(bn_file)

    @staticmethod
    def _create_cpd(var: str, parent_vars: List[str], parsed_cpd: List[float]) -> pd.DataFrame:
        num_parents = len(parent_vars) if parent_vars else 0
        product_list = [[1, 0]] + [[0, 1]] * num_parents

        cpt_idx = list(itertools.product(*product_list))
        cpt_vals = parsed_cpd + [(1 - v) for v in parsed_cpd]

        idx_names = [var]
        if parent_vars:
            idx_names.extend(parent_vars)

        index = pd.MultiIndex.from_tuples(cpt_idx, names=idx_names)
        cpd_df = pd.DataFrame(data=cpt_vals, index=index, columns=["prob"])

        return cpd_df


    @staticmethod
    def parse(file: str) -> Tuple[Dict[str, BayesNode], List[Dict[str, Any]]]:
        """
        Parses the input file and returns an instance of a BayesNet object
        :param file:
        :return: the BayesNet object
        """
        bn_dict: Dict[str, BayesNode] = {}
        query_list: List[Dict[str, Any]] = []

        with open(file) as fin:
            # read the number of vars involved
            # and the number of queries
            N, M = [int(x) for x in next(fin).split()]

            # read the vars, their parents and the CPD
            for i in range(N):
                line = next(fin).split(";")
                parsed_var = line[0].strip()
                parsed_parent_vars = line[1].split()
                parsed_cpd = [float(v) for v in line[2].split()]

                parent_vars = [bn_dict[v] for v in parsed_parent_vars]
                cpd_df = BayesNet._create_cpd(parsed_var, parsed_parent_vars, parsed_cpd)
                bn_dict[parsed_var] = BayesNode(var_name=parsed_var, parent_nodes=parent_vars, cpd=cpd_df)

            # read the queries
            for i in range(M):
                queries, conds = next(fin).split('|')

                query_vars = queries.split()
                query_vars_dict = dict([(q.split("=")[0], q.split("=")[1]) for q in query_vars])

                cond_vars = conds.split()
                cond_vars_dict = dict([(c.split("=")[0], c.split("=")[1]) for c in cond_vars])

                query_list.append({
                    "query": query_vars_dict,
                    "cond": cond_vars_dict
                })

            # read the answers
            for i in range(M):
                query_list[i]["answer"] = float(next(fin).strip())

        return bn_dict, query_list

    def get_graph(self) -> nx.DiGraph:
        bn_graph = nx.DiGraph()

        # add nodes with random var attributes that relate the node name to the BayesNode instance
        # in the bayesian network
        for n in self.nodes:
            bn_graph.add_node(n, bn_var=self.nodes[n])

        # add edges
        for n in self.nodes:
            parent_vars = [v.var_name for v in self.nodes[n].parent_nodes]
            if parent_vars:
                for v in parent_vars:
                    bn_graph.add_edge(v, n)

        return bn_graph

    def prob(self, var_name: str, parent_values: List[int] = None) -> float:
        """
        Function that will get the probability value for the case in which the `var_name' variable is True
        (var_name = 1) and the parent values are given by the list `parent values'
        :param var_name: the variable in the bayesian network for which we are determining the conditional property
        :param parent_values: The list of parent values. Is None if var_name has no parent variables.
        :return:
        """
        if parent_values is None:
            parent_values = []

        index_line = tuple([1] + parent_values)

        return self.nodes[var_name].cpd.loc[index_line]["prob"]

    def sample_log_prob(self, sample: Dict[str, int]):
        logprob = 0
        for var_name in self.nodes:
            var_value = sample[var_name]
            parent_vals = None
            if self.nodes[var_name].parent_nodes:
                parent_names = [parent.var_name for parent in self.nodes[var_name].parent_nodes]
                parent_vals = [sample[pname] for pname in parent_names]

            prob = self.prob(var_name, parent_vals)
            if var_value == 0:
                prob = 1 - prob

            logprob += np.log(prob)

        return logprob

    def sample(self) -> Dict[str, int]:
        """
        Sample values for all the variables in the bayesian network and return them as a dictionary
        :return: A dictionary of var_name, value pairs
        """
        values = {}
        remaining_vars = [var_name for var_name in self.nodes]

        while remaining_vars:
            new_vars = []
            for var_name in remaining_vars:
                parent_vars = [p.var_name for p in self.nodes[var_name].parent_nodes]
                if all(p in values for p in parent_vars):
                    parent_vals = [values[p] for p in parent_vars]
                    prob = self.prob(var_name, parent_vals)
                    values[var_name] = int(np.random.sample() <= prob)
                else:
                    new_vars.append(var_name)
            remaining_vars = new_vars
        return values

    def pretty_print(self):
        res = "Bayesian Network:\n"
        for var_name in self.nodes:
            res += self.nodes[var_name].pretty_print() + "\n"

        return res

    def __str__(self):
        res = "Bayesian Network:\n"
        for var_name in self.nodes:
            res += str(self.nodes[var_name]) + "\n"

        return res

    def __repr__(self):
        return self.__str__()


class JunctionTree:
    """
    Place holder class for the JunctionTree algorithm
    """
    def __init__(self, bn: BayesNet):
        self.bn = bn
        self.clique_tree = self._get_clique_tree()

    def _moralize_graph(self, g: nx.DiGraph) -> nx.Graph:
        pass

    def _triangulate(self, h: nx.Graph) -> nx.Graph:
        pass

    def _create_clique_graph(self, th: nx.Graph) -> nx.Graph:
        pass

    def _extract_clique_tree(self, c: nx.Graph) -> nx.Graph:
        pass

    def _get_clique_tree(self) -> nx.Graph:
        """
        Generate the clique tree which is used to propagate "messages" (run belief propagation)
        within the cliques to balance the clique tree
        :return: The CliqueTree as a nx.DiGraph where each node has an attribute called "factor_vars", which
        is the list of random variables within the clique.
        """
        g = self.bn.get_graph()

        # TODO 1: moralize graph g
        #  see https://networkx.org/documentation/stable/_modules/networkx/algorithms/moral.html
        h = self._moralize_graph(g)

        # TODO 2: triangulate h
        th = self._triangulate(h)

        # TODO 3: create clique graph c - find maximal cliques
        #   see https://networkx.org/documentation/stable/reference/algorithms/chordal.html
        c = self._create_clique_graph(th)

        # TODO 4: create clique tree from clique graph c - find Maximum Weight Spanning Tree in c
        #   see https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.tree.mst.maximum_spanning_tree.html#networkx.algorithms.tree.mst.maximum_spanning_tree
        t = self._extract_clique_tree(c)

        return t

    def _load_factors(self) -> None:
        """
        Compute initial node potentials, by loading the factors from the original bayesian network.
        Each factor from the original bayesian network is assigned to a **single** node in the clique tree,
        with the condition that **all** factor vars be included in the clique node vars.
        """
        raise NotImplementedError("Not implemented by student")

    def _get_junction_tree(self, root_name: str = None) -> nx.DiGraph:
        """
        Set a direction to the edges of the clique tree (which is an nx.Graph) such that the Junction Tree has
        a root. The root node is given by root_name.
        :param root_name: The name of the clique node that is the root of the Junction Tree
        :return: a nx.DiGraph representing the Junction Tree
        """
        if root_name is None or root_name not in self.clique_tree:
            print("Selected root node %s not in clique tree. Choosing randomly." % root_name)
            root_name = random.choice(list(self.clique_tree.nodes()))

        t: nx.DiGraph = nx.bfs_tree(self.clique_tree, root_name)
        clique_tree_attrs = deepcopy(dict(self.clique_tree.nodes(data=True)))
        nx.set_node_attributes(t, clique_tree_attrs)

        return t

    def _incorporate_evidence(self, jt: nx.DiGraph, evidence: Dict[str, int]) -> nx.DiGraph:
        """
        Incorporate the evidence. For each variable in the `evidence' dictionary, choose **one** node of the
        Junction Tree and reduce the factor table (pd.DataFrame) of that node to the set of value combinations (index)
        matching the value of the observed evidence variable.
        :param jt: the initial uncalibrated Junction Tree with factors loaded from the original bayesian network
        :param evidence: a dictionary of observed variables

        :return: The uncalibrated junction tree with incorporated evidence
        """
        raise NotImplementedError("Not implemented by student")

    def _run_belief_propagation(self, uncalibrated_jt) -> nx.DiGraph:
        """
        Run the upward and downward passes in the Belief propagation algorithm to calibrate
        :param uncalibrated_jt: The uncalibrated Junction Tree obtained after incorporating the evidence
        :return: The calibrated Junction tree
        """
        raise NotImplementedError("Not implemented by student")

    def _eval_query(self, calibrated_jt: nx.DiGraph, query: Dict[str, int]) -> float:
        """
        Evaluate the query by distinguishing between within- or out-of-clique queries.
        :param calibrated_jt: The calibrated Junction Tree
        :return: the float value for the probability of the query
        """

    def run_query(self, query: Dict[str, int], evidence: Dict[str, int]) -> float:
        # TODO: select a non-None root
        root_name = None

        # get junction tree copy
        jt = self._get_junction_tree(root_name=root_name)

        # incorporate evidence
        uncalibrared_jt = self._incorporate_evidence(jt, evidence)

        # calibrate tree
        calibrated_jt = self._run_belief_propagation(uncalibrared_jt)

        return self._eval_query(calibrated_jt, query)

    def run_queries(self, queries) -> None:
        """
        Run queries.
        :param queries: queries in the original bayesian network
        """
        for query in queries:
            query_prob = self.run_query(query["query"], query["cond"])
            if almost_equal(query_prob, query["answer"]):
                print("Query %s OK. Answer is %.6f, given result is %.6f" % (str(query), query["answer"], query_prob))
            else:
                print(
                    "Query %s NOT OK. Answer is %.6f, given result is %.6f" % (str(query), query["answer"], query_prob))


if __name__ == "__main__":
    bn = BayesNet(bn_file="data/bnet")
    jt = JunctionTree(bn=bn)
    jt.run_queries(bn.queries)