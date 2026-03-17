from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import Dict, List, Tuple

VertexId = int
Edge = Tuple[VertexId, VertexId]
Point = Tuple[float, float]
Axial = Tuple[int, int]


class HexResource(Enum):
    BRICK = "brick"
    LUMBER = "lumber"
    WOOL = "wool"
    GRAIN = "grain"
    ORE = "ore"
    DESERT = "desert"


@dataclass
class Board:
    edges: List[Edge]
    vertex_neighbors: List[List[int]]
    vertex_edges: List[List[int]]

    hex_vertices: List[List[int]]      # hex_id -> 6 vertex_id
    hex_centers: List[Point]           # hex_id -> center (x, y)
    vertex_positions: List[Point]      # vertex_id -> (x, y)

    hex_resources: List[HexResource]   # hex_id -> resource type
    hex_numbers: List[int | None]      # hex_id -> dice number, None for desert


def _round_point(p: Point, digits: int = 6) -> Point:
    return (round(p[0], digits), round(p[1], digits))


def _hex_corners(center: Point, size: float) -> List[Point]:
    """
    Zwraca 6 narożników heksa typu pointy-top
    w kolejności:
    top, top-right, bottom-right, bottom, bottom-left, top-left
    """
    cx, cy = center

    corners = [
        (cx, cy - size),
        (cx + sqrt(3) / 2 * size, cy - 0.5 * size),
        (cx + sqrt(3) / 2 * size, cy + 0.5 * size),
        (cx, cy + size),
        (cx - sqrt(3) / 2 * size, cy + 0.5 * size),
        (cx - sqrt(3) / 2 * size, cy - 0.5 * size),
    ]

    return [_round_point(p) for p in corners]


def _axial_to_pixel(q: int, r: int, size: float) -> Point:
    """
    Konwersja axial -> pixel dla pointy-top heksów.
    Tu nie zaokrąglamy, żeby nie psuć wspólnych narożników.
    """
    x = sqrt(3) * size * (q + r / 2)
    y = 1.5 * size * r
    return (x, y)


def _standard_catan_axial_coords() -> List[Axial]:
    """
    Standardowa plansza 19 heksów jako hexagon radius 2.
    Warunek:
        max(|q|, |r|, |s|) <= 2
    gdzie:
        s = -q-r
    """
    coords: List[Axial] = []
    radius = 2

    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= radius:
                coords.append((q, r))

    # stabilna kolejność
    coords.sort(key=lambda x: (x[1], x[0]))
    return coords


def _default_hex_resources() -> List[HexResource]:
    """
    Stały testowy układ zasobów dla 19 heksów.
    Kolejność odpowiada kolejności hexów generowanych przez planszę.
    """
    return [
        HexResource.WOOL,
        HexResource.ORE,
        HexResource.LUMBER,
        HexResource.GRAIN,
        HexResource.BRICK,
        HexResource.WOOL,
        HexResource.LUMBER,
        HexResource.DESERT,
        HexResource.GRAIN,
        HexResource.BRICK,
        HexResource.ORE,
        HexResource.WOOL,
        HexResource.GRAIN,
        HexResource.LUMBER,
        HexResource.BRICK,
        HexResource.ORE,
        HexResource.GRAIN,
        HexResource.WOOL,
        HexResource.LUMBER,
    ]


def _default_hex_numbers(resources: List[HexResource]) -> List[int | None]:
    """
    Standardowy zestaw numerów Catana.
    Pustynia dostaje None.
    """
    available_numbers = [
        5, 2, 6, 3, 8, 10, 9, 12, 11,
        4, 8, 10, 9, 4, 5, 6, 3, 11
    ]

    numbers: List[int | None] = []
    idx = 0

    for resource in resources:
        if resource == HexResource.DESERT:
            numbers.append(None)
        else:
            numbers.append(available_numbers[idx])
            idx += 1

    return numbers


def create_full_board(size: float = 1.0) -> Board:
    """
    Tworzy pełną planszę standardowego Catana:
    - 19 heksów
    - 54 wierzchołki
    - 72 krawędzie
    """
    axial_coords = _standard_catan_axial_coords()
    hex_centers = [_axial_to_pixel(q, r, size) for q, r in axial_coords]

    vertex_map: Dict[Point, int] = {}
    vertex_positions: List[Point] = []
    hex_vertices: List[List[int]] = []

    # 1. Zbuduj unikalne wierzchołki
    for center in hex_centers:
        corners = _hex_corners(center, size)
        current_hex_vertices: List[int] = []

        for corner in corners:
            if corner not in vertex_map:
                vertex_id = len(vertex_positions)
                vertex_map[corner] = vertex_id
                vertex_positions.append(corner)
            current_hex_vertices.append(vertex_map[corner])

        hex_vertices.append(current_hex_vertices)

    # 2. Zbuduj unikalne krawędzie
    edge_map: Dict[Tuple[int, int], int] = {}
    edges: List[Edge] = []

    for hv in hex_vertices:
        for i in range(6):
            a = hv[i]
            b = hv[(i + 1) % 6]
            edge = tuple(sorted((a, b)))

            if edge not in edge_map:
                edge_map[edge] = len(edges)
                edges.append(edge)

    # 3. Sąsiedztwa
    num_vertices = len(vertex_positions)
    vertex_neighbors = [[] for _ in range(num_vertices)]
    vertex_edges = [[] for _ in range(num_vertices)]

    for edge_id, (a, b) in enumerate(edges):
        vertex_neighbors[a].append(b)
        vertex_neighbors[b].append(a)

        vertex_edges[a].append(edge_id)
        vertex_edges[b].append(edge_id)

    # 4. Dane heksów
    hex_resources = _default_hex_resources()
    hex_numbers = _default_hex_numbers(hex_resources)

    rounded_centers = [_round_point(c) for c in hex_centers]

    return Board(
        edges=edges,
        vertex_neighbors=vertex_neighbors,
        vertex_edges=vertex_edges,
        hex_vertices=hex_vertices,
        hex_centers=rounded_centers,
        vertex_positions=vertex_positions,
        hex_resources=hex_resources,
        hex_numbers=hex_numbers,
    )