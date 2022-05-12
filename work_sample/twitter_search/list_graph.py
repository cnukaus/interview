class SimpleGraph:
    """
    list_graph implement graph in a dictionary with dict value is a list of [edges,weight]
    https://www.educative.io/edpresso/how-to-implement-a-graph-in-python
    """

    def __init__(self):
        self.graph = {}
        self.vertices_no = 0

    def add_vertex(self, v, verbose=False):

        if v in self.graph:
            if verbose:
                print("Vertex ", v, " already exists.")
        else:
            self.vertices_no = self.vertices_no + 1
            self.graph[v] = []

    # modify edge value, between vertex v1 and v2, add e
    def add_edge(self, v1, v2, e, verbose=False):

        # Check if vertex v1 is a valid vertex
        if v1 not in self.graph:
            if verbose:
                print("Vertex ", v1, " does not exist.")
        # Check if vertex v2 is a valid vertex
        elif v2 not in self.graph:
            if verbose:
                print("Vertex v2", v2, " does not exist.")
        else:
            # Since this code is not restricted to a directed or
            # an undirected graph, an edge between v1 v2 does not
            # imply that an edge exists between v2 and v1
            temp = [v2, e]
            found = False
            for edge in self.graph[v1]:
                if edge[0] == v2:
                    edge[1] += e
                    found = True
            if not found:
                self.graph[v1].append(temp)

    # Print the graph
    def print_graph(self, min_weight=1, search_vertex=None):

        for vertex in self.graph:
            for edges in self.graph[vertex]:
                if edges[1] >= min_weight:
                    if search_vertex:
                        if search_vertex == vertex:
                            print(
                                "search found ",
                                vertex,
                                " -> ",
                                edges[0],
                                " edge weight: ",
                                edges[1],
                            )
                        continue
                    print(vertex, " -> ", edges[0], " edge weight: ", edges[1])
