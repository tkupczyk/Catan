from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import Dict, List, Tuple
import random
import math

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

class PortType(Enum):
    THREE_TO_ONE = "3:1"
    BRICK = "brick"
    LUMBER = "lumber"
    WOOL = "wool"
    GRAIN = "grain"
    ORE = "ore"

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

    ports: List[Tuple[Tuple[int, int], PortType]]   # [((v1, v2), port_type), ...]


def _round_point(p: Point, digits: int = 6) -> Point:
    return (round(p[0], digits), round(p[1], digits))


def _create_ports(hex_vertices: List[List[int]], vertex_positions: List[Point]) -> List[Tuple[Tuple[int, int], PortType]]:
    """
    Tworzy 9 portów na krawędziach zewnętrznych planszy.
    Port jest przypisany do pary sąsiednich vertexów na brzegu.
    To wersja deterministyczna oparta o geometrię planszy.
    """
    # policz, które krawędzie należą tylko do jednego heksa = zewnętrzne
    edge_counts: Dict[Tuple[int, int], int] = {}
    for hv in hex_vertices:
        for i in range(6):
            a = hv[i]
            b = hv[(i + 1) % 6]
            e = tuple(sorted((a, b)))
            edge_counts[e] = edge_counts.get(e, 0) + 1

    boundary_edges = [e for e, count in edge_counts.items() if count == 1]

    # sortowanie po kącie środka krawędzi względem środka planszy
    cx = sum(x for x, _ in vertex_positions) / len(vertex_positions)
    cy = sum(y for _, y in vertex_positions) / len(vertex_positions)

    def edge_angle(edge):
        a, b = edge
        x = (vertex_positions[a][0] + vertex_positions[b][0]) / 2
        y = (vertex_positions[a][1] + vertex_positions[b][1]) / 2
        return math.atan2(y - cy, x - cx)

    boundary_edges.sort(key=edge_angle)

    # wybieramy 9 krawędzi mniej więcej równomiernie po okręgu
    if len(boundary_edges) < 9:
        raise ValueError("Za mało krawędzi brzegowych do przypisania portów.")

    step = len(boundary_edges) / 9
    chosen_edges = []
    used = set()

    for i in range(9):
        idx = int(round(i * step)) % len(boundary_edges)
        # znajdź najbliższą nieużytą
        for shift in range(len(boundary_edges)):
            j = (idx + shift) % len(boundary_edges)
            if j not in used:
                used.add(j)
                chosen_edges.append(boundary_edges[j])
                break

    port_types = [
        PortType.THREE_TO_ONE,
        PortType.THREE_TO_ONE,
        PortType.THREE_TO_ONE,
        PortType.THREE_TO_ONE,
        PortType.BRICK,
        PortType.LUMBER,
        PortType.WOOL,
        PortType.GRAIN,
        PortType.ORE,
    ]

    # można potem losować; na razie stabilnie
    return list(zip(chosen_edges, port_types))

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

def _hex_adjacency(hex_vertices: List[List[int]]) -> List[List[int]]:
    """
    Zwraca listę sąsiadów dla każdego heksa.
    Dwa heksy są sąsiadami jeśli dzielą co najmniej 2 wierzchołki.
    """
    n = len(hex_vertices)
    neighbors = [[] for _ in range(n)]

    for i in range(n):
        vi = set(hex_vertices[i])
        for j in range(i + 1, n):
            vj = set(hex_vertices[j])
            if len(vi & vj) >= 2:
                neighbors[i].append(j)
                neighbors[j].append(i)

    return neighbors

def _valid_number_layout(numbers: List[int | None], neighbors: List[List[int]]) -> bool:
    """
    Sprawdza czy 6 i 8 nie są obok siebie.
    """
    for i, num in enumerate(numbers):
        if num not in (6, 8):
            continue

        for j in neighbors[i]:
            if numbers[j] in (6, 8):
                return False

    return True

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


def _random_hex_resources(rng: random.Random) -> List[HexResource]:
    """
    Losowy układ zasobów zgodny ze standardowym Catanem:
    - 4 lumber
    - 4 wool
    - 4 grain
    - 3 brick
    - 3 ore
    - 1 desert
    """
    resources = (
        [HexResource.LUMBER] * 4 +
        [HexResource.WOOL] * 4 +
        [HexResource.GRAIN] * 4 +
        [HexResource.BRICK] * 3 +
        [HexResource.ORE] * 3 +
        [HexResource.DESERT]
    )
    rng.shuffle(resources)
    return resources


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


def _random_hex_numbers(resources: List[HexResource],
                        hex_vertices: List[List[int]],
                        rng: random.Random) -> List[int | None]:
    """
    Losuje numery tak, żeby 6 i 8 nie były sąsiadami.
    """
    available_numbers = [
        2, 3, 3, 4, 4, 5, 5, 6, 6,
        8, 8, 9, 9, 10, 10, 11, 11, 12
    ]

    neighbors = _hex_adjacency(hex_vertices)

    while True:
        rng.shuffle(available_numbers)

        numbers: List[int | None] = []
        idx = 0

        for resource in resources:
            if resource == HexResource.DESERT:
                numbers.append(None)
            else:
                numbers.append(available_numbers[idx])
                idx += 1

        if _valid_number_layout(numbers, neighbors):
            return numbers


def create_full_board(
    size: float = 1.0,
    randomize: bool = True,
    seed: int | None = None,
) -> Board:
    """
    Tworzy pełną planszę standardowego Catana:
    - 19 heksów
    - 54 wierzchołki
    - 72 krawędzie

    Parametry:
    - randomize=True  -> losowe zasoby i numery
    - randomize=False -> stały układ testowy
    - seed            -> opcjonalny seed do debugowania
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
    rng = random.Random(seed)

    if randomize:
        hex_resources = _random_hex_resources(rng)
        hex_numbers = _random_hex_numbers(hex_resources, hex_vertices, rng)
    else:
        hex_resources = _default_hex_resources()
        hex_numbers = _default_hex_numbers(hex_resources)

    rounded_centers = [_round_point(c) for c in hex_centers]

    ports = _create_ports(hex_vertices, vertex_positions)

    return Board(
        edges=edges,
        vertex_neighbors=vertex_neighbors,
        vertex_edges=vertex_edges,
        hex_vertices=hex_vertices,
        hex_centers=rounded_centers,
        vertex_positions=vertex_positions,
        hex_resources=hex_resources,
        hex_numbers=hex_numbers,
        ports=ports,
    )