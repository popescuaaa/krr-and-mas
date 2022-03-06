class Parser(object):
    @staticmethod
    def parse(file: str):
        """
        @param file: path to the input file
        :returns Bayesian network as a dictionary {node: [list of parents], ...}
        and the list of queries as [{"X": [list of vars],
        "Y": [list of vars], "Z": [list of vars]}, ... ] where we want
        to test the conditional independence of vars1 ⊥ vars2 | cond
        """

        bn = {}
        queries = []

        with open(file) as fin:
            # read the number of vars involved
            # and the number of queries
            N, M = [int(x) for x in next(fin).split()]

            # read the vars and their parents
            for i in range(N):
                line = next(fin).split()
                var, parents = line[0], line[1:]
                bn[var] = parents

            # read the queries
            for i in range(M):
                vars, cond = next(fin).split('|')

                # parse vars
                X, Y = vars.split(';')
                X = X.split()
                Y = Y.split()

                # parse cond
                Z = cond.split()

                queries.append({
                    "X": X,
                    "Y": Y,
                    "Z": Z
                })

            # read the answers
            for i in range(M):
                queries[i]["answer"] = next(fin).strip()

        return bn, queries

    @staticmethod
    def get_graph(bn: dict):
        '''
        @param bn: Bayesian netowrk obtained from parse
        :returns the graph as {node: [list of children], ...}
        '''
        graph = {}

        _parents = {}  # invereted bn

        for node in bn:
            parents = bn[node]
            _parents[node] = parents

            # this is for the leafs
            if node not in graph:
                graph[node] = []

            # for each parent add
            # the edge parent->node
            for p in parents:
                if p not in graph:
                    graph[p] = []
                graph[p].append(node)

        return graph, _parents


def dfs(node, X, Y, curr_path, parents, graph):
    curr_path = curr_path.copy()
    curr_path.append(node)

    if node in Y:
        return [curr_path]

    result = []

    for v in parents[node]:
        if v not in curr_path and not v in X:
            result.extend(dfs(v, X, Y, curr_path, parents, graph))

    for v in graph[node]:
        if v not in curr_path and not v in X:
            result.extend(dfs(v, X, Y, curr_path, parents, graph))

    return result


def path_active_given_z(path, parents, Z):
    for i in range(len(path) - 2):
        prev = path[i]
        curr = path[i + 1]
        next = path[i + 2]

        active_causal = False
        active_evidential = False
        active_cause = False
        active_effect = False

        if prev in parents[curr] and curr in parents[next] and curr not in Z:
            active_causal = True
        if curr in parents[prev] and next in parents[curr] and curr not in Z:
            active_evidential = True
        if curr in parents[prev] and curr in parents[next] and curr not in Z:
            active_cause = True
        if prev in parents[curr] and next in parents[curr] and curr in Z:
            active_effect = True

        if not active_causal and not active_evidential and not active_cause and not active_effect:
            return False

    return True


def run_inferences(query, parents, graph):
    X = query["X"]
    Y = query["Y"]
    Z = query["Z"]

    a_to_b_paths = []
    for x in X:
        a_to_b_paths.extend(dfs(x, X, Y, [], parents, graph))

    is_active = False
    for path in a_to_b_paths:
        if path_active_given_z(path, parents, Z):
            is_active = True
            break
    if is_active:
        print("false")
    else:
        print("true")


if __name__ == "__main__":
    from pprint import pprint

    # example usage
    bn, queries = Parser.parse("bn1")
    graph, p = Parser.get_graph(bn)

    # print("Bayesian Network\n" + "-" * 50)
    # pprint(bn)
    #
    # print("\nQueries\n" + "-" * 50)
    # pprint(queries)
    #
    # print("\nGraph\n" + "-" * 50)
    # pprint(graph)

    for q in queries:
        print("\nQuery\n" + "-" * 50)
        pprint(q)
        run_inferences(q, p, graph)

