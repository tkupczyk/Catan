from dataclasses import dataclass
from typing import List, Tuple

VertexId = int
Edge = Tuple[VertexId, VertexId]


@dataclass
class Board:
    edges: List[Edge]
    vertex_neighbors: List[List[int]]
    vertex_edges: List[List[int]]


def create_test_board() -> Board:

    edges = [
        (0, 1),
        (1, 2),
        (0, 3),
        (1, 3),
    ]

    num_vertices = 4

    neighbors = [[] for _ in range(num_vertices)]
    vertex_edges = [[] for _ in range(num_vertices)]

    for eid, (a, b) in enumerate(edges):
        neighbors[a].append(b)
        neighbors[b].append(a)

        vertex_edges[a].append(eid)
        vertex_edges[b].append(eid)

    return Board(
        edges=edges,
        vertex_neighbors=neighbors,
        vertex_edges=vertex_edges
    )