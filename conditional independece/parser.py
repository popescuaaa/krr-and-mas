class Parser(object):
	@staticmethod
	def parse(file: str):
		'''
		@param file: path to the input file
		:returns Bayesian network as a dictionary {node: [list of parents], ...}
		and the list of queries as [{"X": [list of vars], 
		"Y": [list of vars], "Z": [list of vars]}, ... ] where we want 
		to test the conditional independence of vars1 ⊥ vars2 | cond 
		'''
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

		for node in bn:
			parents = bn[node]

			# this is for the leafs
			if node not in graph:
				graph[node] = []

			# for each parent add 
			# the edge parent->node
			for p in parents:
				if p not in graph:
					graph[p] = []
				graph[p].append(node)

		return graph



if __name__ == "__main__":
	from pprint import pprint
	
	# example usage
	bn, queries = Parser.parse("bn1")
	graph = Parser.get_graph(bn)
	
	print("Bayesian Network\n" + "-" * 50)
	pprint(bn)

	print("\nQueries\n" + "-" * 50)
	pprint(queries)

	print("\nGraph\n" + "-" * 50)
	pprint(graph)