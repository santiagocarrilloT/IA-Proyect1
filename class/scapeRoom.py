from node import Node

class ScapeRoom:
    def __init__ (self):
        self.nodes = {}
        self.start = None
        self.goal = None

    def add_node (self, name, isLocked=False, isPuzzle=False):
        self.nodes[name] = Node(name, isLocked, isPuzzle)

    def add_edge (self, from_node, to_name, cost=1):
        self.nodes[from_node].neighbors.append((self.nodes[to_name], cost))