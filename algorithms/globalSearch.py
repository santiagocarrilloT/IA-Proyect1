# A* Function
def a_star_search(tree, start, goal):
    open_set = {start}
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
        if current == goal:
            return reconstruct_path(came_from, current)

        open_set.remove(current)
        for neighbor in tree.get(current, []):
            tentative_g_score = g_score.get(current, float('inf')) + 1
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                open_set.add(neighbor)

    return None

# Heuristic function (Manhattan distance)
def heuristic(a, b):
    return abs(ord(a) - ord(b))

# Recursive DFS function
def dfs_recursive(tree, node, visited=None):
    if visited is None:
        visited = set()  # Initialize the visited set
    visited.add(node)    # Mark the node as visited
    print(node)          # Print the current node (for illustration)
    for child in tree[node]:  # Recursively visit children
        if child not in visited:
            dfs_recursive(tree, child, visited)

# Run DFS starting from node 'A'

# Define subtree B
subTreeB = {
    'B': ['D', 'E'],
    'D': ['H', 'I'],
    'E': ['J', 'K'],
    'H': [], 'I': [], 'J': [], 'K': [],
}
# Define the decision tree as a dictionary
tree = {
    'A': [subTreeB, 'C'],
    #'B': ['D', 'E'],
    'C': ['F', 'G'],
    'D': ['H', 'I'],
    'E': ['J', 'K'],
    'F': ['L', 'M'],
    'G': ['N', 'O'],
    'H': [], 'I': [], 'J': [], 'K': [],
    'L': [], 'M': [], 'N': [], 'O': []
}

dfs_recursive(tree, 'A')

