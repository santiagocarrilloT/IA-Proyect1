#Usado para búsqueda informada (A)*
#Representa a un determinado nodo en la cola

"""
f(n) = g(n) + h(n)
Se ordena a razón de f(n) y se eliminan comparaciones con g(n) o h(n).
"""

from dataclasses import dataclass, field

@dataclass(order=True)
class AStarNode:
    f: float
    g: float = field(compare=False)
    h: float = field(compare=False)
    node_id: str = field(compare=False)
    path: list[str] = field(compare=False, default_factory=list)