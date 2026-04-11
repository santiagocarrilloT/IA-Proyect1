class Node:
    def __init__ (self, name, isLocked=False, isPuzzle=False):
        self.name = name
        self.isLocked = isLocked
        self.isUnlocked = False
        self.isPuzzle = isPuzzle
        self.neighbors = []