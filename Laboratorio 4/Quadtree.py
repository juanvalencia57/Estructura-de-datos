from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from random import Random
from typing import Any, Iterable, Iterator, Optional


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    data: Any = None


@dataclass(frozen=True)
class Rectangle:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def contains(self, point: Point) -> bool:
        return (
            self.xmin <= point.x <= self.xmax
            and self.ymin <= point.y <= self.ymax
        )

    def intersects_circle(self, x: float, y: float, radius: float) -> bool:
        closest_x = min(max(x, self.xmin), self.xmax)
        closest_y = min(max(y, self.ymin), self.ymax)
        return (closest_x - x) ** 2 + (closest_y - y) ** 2 <= radius**2


class Quadtree:
    def __init__(
        self,
        boundary: Rectangle,
        capacity: int = 3,
        max_depth: int = 32,
        depth: int = 0,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity debe ser positiva")
        if boundary.xmin > boundary.xmax or boundary.ymin > boundary.ymax:
            raise ValueError("los límites del rectángulo no son válidos")
        self.boundary = boundary
        self.capacity = capacity
        self.max_depth = max_depth
        self.depth = depth
        self.points: list[Point] = []
        self.children: Optional[tuple[Quadtree, Quadtree, Quadtree, Quadtree]] = None

    def insert(self, point: Point) -> bool:
        if not self.boundary.contains(point):
            return False
        if self.children is None:
            if len(self.points) < self.capacity or self.depth >= self.max_depth:
                self.points.append(point)
                return True
            # La hoja ya tiene capacity puntos: el punto nuevo provoca
            # exactamente una subdivisión antes de redistribuirlos.
            self._subdivide()
            old_points = self.points
            self.points = []
            for old_point in old_points:
                self._insert_into_child(old_point)
        return self._insert_into_child(point)

    def _subdivide(self) -> None:
        mid_x = (self.boundary.xmin + self.boundary.xmax) / 2
        mid_y = (self.boundary.ymin + self.boundary.ymax) / 2
        b = self.boundary
        self.children = (
            Quadtree(Rectangle(b.xmin, b.ymin, mid_x, mid_y), self.capacity, self.max_depth, self.depth + 1),
            Quadtree(Rectangle(mid_x, b.ymin, b.xmax, mid_y), self.capacity, self.max_depth, self.depth + 1),
            Quadtree(Rectangle(b.xmin, mid_y, mid_x, b.ymax), self.capacity, self.max_depth, self.depth + 1),
            Quadtree(Rectangle(mid_x, mid_y, b.xmax, b.ymax), self.capacity, self.max_depth, self.depth + 1),
        )

    def _insert_into_child(self, point: Point) -> bool:
        assert self.children is not None
        for child in self.children:
            if child.insert(point):
                return True
        return False

    def range_search(self, x: float, y: float, radius: float) -> list[Point]:
        if radius < 0:
            raise ValueError("radius no puede ser negativo")
        if not self.boundary.intersects_circle(x, y, radius):
            return []
        radius_squared = radius**2
        result = [
            point
            for point in self.points
            if (point.x - x) ** 2 + (point.y - y) ** 2 <= radius_squared
        ]
        if self.children is not None:
            for child in self.children:
                result.extend(child.range_search(x, y, radius))
        return result

    def nearest(self, x: float, y: float) -> Optional[Point]:
        """Encuentra el vecino más cercano mediante poda por distancia al rectángulo."""
        best: Optional[Point] = None
        best_distance_squared = float("inf")

        def visit(node: Quadtree) -> None:
            nonlocal best, best_distance_squared
            if not node.boundary.intersects_circle(
                x, y, best_distance_squared**0.5
            ):
                return
            for point in node.points:
                distance_squared = (point.x - x) ** 2 + (point.y - y) ** 2
                if distance_squared < best_distance_squared:
                    best, best_distance_squared = point, distance_squared
            if node.children is not None:
                ordered = sorted(
                    node.children,
                    key=lambda child: _rectangle_distance_squared(child.boundary, x, y),
                )
                for child in ordered:
                    visit(child)

        visit(self)
        return best

    def __len__(self) -> int:
        return len(self.points) + (
            sum(len(child) for child in self.children) if self.children else 0
        )

    def iter_nodes(self, max_depth: Optional[int] = None) -> Iterator["Quadtree"]:
        """Recorre nodos para inspeccionar o visualizar las subdivisiones."""
        if max_depth is None or self.depth <= max_depth:
            yield self
        if self.children is not None and (
            max_depth is None or self.depth < max_depth
        ):
            for child in self.children:
                yield from child.iter_nodes(max_depth)

    def iter_leaves(self) -> Iterator["Quadtree"]:
        if self.children is None:
            yield self
            return
        for child in self.children:
            yield from child.iter_leaves()

    def statistics(self) -> dict[str, int]:
        nodes = list(self.iter_nodes())
        leaves = [node for node in nodes if node.children is None]
        return {
            "nodes": len(nodes),
            "leaves": len(leaves),
            "max_depth": max((node.depth for node in nodes), default=0),
            "stored_points": sum(len(node.points) for node in leaves),
            "max_leaf_points": max((len(node.points) for node in leaves), default=0),
        }


def _rectangle_distance_squared(rectangle: Rectangle, x: float, y: float) -> float:
    dx = max(rectangle.xmin - x, 0, x - rectangle.xmax)
    dy = max(rectangle.ymin - y, 0, y - rectangle.ymax)
    return dx * dx + dy * dy


def build_quadtree(points: Iterable[Point], boundary: Rectangle, capacity: int = 3) -> Quadtree:
    tree = Quadtree(boundary, capacity=capacity)
    for point in points:
        if not tree.insert(point):
            raise ValueError(f"el punto está fuera del límite: {point}")
    return tree


def generate_points(count: int = 10_000, side: float = 10_000.0, seed: int = 2026) -> list[Point]:
    generator = Random(seed)
    return [
        Point(generator.uniform(0, side), generator.uniform(0, side), index)
        for index in range(count)
    ]


def brute_force_range(points: Iterable[Point], x: float, y: float, radius: float) -> list[Point]:
    radius_squared = radius**2
    return [
        point
        for point in points
        if (point.x - x) ** 2 + (point.y - y) ** 2 <= radius_squared
    ]


def brute_force_nearest(points: Iterable[Point], x: float, y: float) -> Optional[Point]:
    return min(
        points,
        key=lambda point: (point.x - x) ** 2 + (point.y - y) ** 2,
        default=None,
    )


def distance(a: Point, b: Point) -> float:
    return hypot(a.x - b.x, a.y - b.y)
