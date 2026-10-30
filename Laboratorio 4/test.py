import unittest
import os
from random import Random
from pathlib import Path
from typing import Optional

from Quadtree import (
    Point,
    Rectangle,
    brute_force_nearest,
    brute_force_range,
    build_quadtree,
    generate_points,
)


ROOT = Path(__file__).parent


class QuadtreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.points = generate_points(10_000)
        self.tree = build_quadtree(self.points, Rectangle(0, 0, 10_000, 10_000))

    def test_inserta_todos_los_puntos(self) -> None:
        self.assertEqual(len(self.tree), len(self.points))

    def test_divisiones_y_distribucion_son_validas(self) -> None:
        stats = self.tree.statistics()
        self.assertGreater(stats["nodes"], 1)
        self.assertGreater(stats["leaves"], 1)
        self.assertEqual(stats["stored_points"], len(self.points))
        self.assertLessEqual(stats["max_leaf_points"], self.tree.capacity)
        for node in self.tree.iter_nodes():
            for point in node.points:
                self.assertTrue(node.boundary.contains(point))

    def test_la_subdivision_ocurre_al_superar_la_capacidad(self) -> None:
        points = [Point(float(index), 0, index) for index in range(4)]
        tree = build_quadtree(points, Rectangle(0, -1, 3, 1), capacity=3)
        self.assertIsNotNone(tree.children)
        self.assertEqual(tree.points, [])
        self.assertEqual(len(tree), 4)

    def test_range_search_coincide_con_fuerza_bruta(self) -> None:
        query = (4_800, 5_200, 500)
        tree_ids = {point.data for point in self.tree.range_search(*query)}
        brute_ids = {point.data for point in brute_force_range(self.points, *query)}
        self.assertEqual(tree_ids, brute_ids)

    def test_nearest_coincide_con_fuerza_bruta(self) -> None:
        query = (1_234, 8_765)
        self.assertEqual(
            self.tree.nearest(*query).data,
            brute_force_nearest(self.points, *query).data,
        )

    def test_punto_en_borde_y_radio_cero(self) -> None:
        points = [Point(0, 0, "origen"), Point(10, 10, "esquina")]
        tree = build_quadtree(points, Rectangle(0, 0, 10, 10), capacity=1)
        self.assertEqual(tree.range_search(0, 0, 0)[0].data, "origen")
        self.assertEqual(tree.nearest(10, 10).data, "esquina")

    def test_rechaza_radio_negativo_y_punto_fuera(self) -> None:
        tree = build_quadtree([], Rectangle(0, 0, 10, 10))
        with self.assertRaises(ValueError):
            tree.range_search(0, 0, -1)
        self.assertFalse(tree.insert(Point(20, 20)))


def create_visualizations(seed: Optional[int] = None) -> None:
    """Crea las figuras solicitadas; requiere matplotlib."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle as PlotRectangle

    points = generate_points(10_000)
    tree = build_quadtree(points, Rectangle(0, 0, 10_000, 10_000))
    random = Random(seed)
    qx = random.uniform(0, 10_000)
    qy = random.uniform(0, 10_000)
    radius = 500
    neighbors = tree.range_search(qx, qy, radius)
    nearest = tree.nearest(qx, qy)
    leaves = list(tree.iter_leaves())
    query_leaf = next(leaf for leaf in leaves if leaf.boundary.contains(Point(qx, qy)))
    print(
        f"Consulta: ({qx:.2f}, {qy:.2f}) m | "
        f"radio: {radius} m | vecinos encontrados: {len(neighbors)} | "
        f"más cercano: {nearest.data if nearest else 'ninguno'}"
    )
    fig, axis = plt.subplots(figsize=(8, 8))
    for leaf in leaves:
        rectangle = leaf.boundary
        intersects = rectangle.intersects_circle(qx, qy, radius)
        axis.add_patch(
            PlotRectangle(
                (rectangle.xmin, rectangle.ymin),
                rectangle.xmax - rectangle.xmin,
                rectangle.ymax - rectangle.ymin,
                facecolor="gold" if intersects else "none",
                edgecolor="darkorange" if intersects else "lightgray",
                linewidth=0.9 if intersects else 0.35,
                alpha=0.18 if intersects else 0.7,
                zorder=1,
            )
        )
    axis.scatter(
        [p.x for p in points], [p.y for p in points],
        s=2, alpha=0.2, color="gray", label="Entregas", zorder=2
    )
    axis.scatter(
        [p.x for p in neighbors], [p.y for p in neighbors],
        s=2, color="royalblue", label="Vecinos dentro de 500 m", zorder=3
    )
    axis.scatter(
        [qx], [qy], s=2, color="crimson",
        label="Punto de referencia", zorder=5
    )
    axis.add_patch(
        Circle((qx, qy), radius, fill=False, color="crimson", linewidth=2, zorder=4)
    )
    axis.add_patch(
        PlotRectangle(
            (query_leaf.boundary.xmin, query_leaf.boundary.ymin),
            query_leaf.boundary.xmax - query_leaf.boundary.xmin,
            query_leaf.boundary.ymax - query_leaf.boundary.ymin,
            facecolor="crimson",
            edgecolor="crimson",
            alpha=0.22,
            linewidth=2,
            label="Subdivisión de referencia",
            zorder=1,
        )
    )
    axis.set(
        title="Range search y subdivisiones del Quadtree",
        xlabel="x (m)", ylabel="y (m)", xlim=(0, 10_000), ylim=(0, 10_000)
    )
    axis.set_aspect("equal")
    axis.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(ROOT / "radio_vecinos.png", dpi=150)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8, 8))
    for leaf in leaves:
        rectangle = leaf.boundary
        axis.add_patch(
            PlotRectangle(
                (rectangle.xmin, rectangle.ymin),
                rectangle.xmax - rectangle.xmin,
                rectangle.ymax - rectangle.ymin,
                fill=False,
                edgecolor="lightgray",
                linewidth=0.35,
                alpha=0.7,
                zorder=1,
            )
        )
    axis.add_patch(
        PlotRectangle(
            (query_leaf.boundary.xmin, query_leaf.boundary.ymin),
            query_leaf.boundary.xmax - query_leaf.boundary.xmin,
            query_leaf.boundary.ymax - query_leaf.boundary.ymin,
            facecolor="gold",
            edgecolor="darkorange",
            alpha=0.3,
            linewidth=2,
            label="Subdivisión de referencia",
            zorder=1,
        )
    )
    axis.scatter(
        [p.x for p in points], [p.y for p in points],
        s=2, alpha=0.2, color="gray", label="Entregas", zorder=2
    )
    axis.scatter(
        [qx], [qy], s=2, color="crimson",
        label="Punto de referencia", zorder=5
    )
    axis.scatter(
        [nearest.x], [nearest.y], s=2, color="limegreen",
        label="Vecino más cercano", zorder=5
    )
    axis.plot(
        [qx, nearest.x], [qy, nearest.y],
        color="limegreen", linewidth=2, label="Distancia", zorder=4
    )
    axis.set(
        title="Vecino más cercano y subdivisiones del Quadtree",
        xlabel="x (m)", ylabel="y (m)", xlim=(0, 10_000), ylim=(0, 10_000)
    )
    axis.set_aspect("equal")
    axis.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(ROOT / "vecino_mas_cercano.png", dpi=150)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10, 10))
    axis.scatter(
        [p.x for p in points],
        [p.y for p in points],
        s=1,
        alpha=0.12,
        color="black",
        label="Puntos",
    )
    leaves = list(tree.iter_leaves())
    max_depth = max(leaf.depth for leaf in leaves)
    colormap = plt.get_cmap("viridis")
    for leaf in leaves:
        rectangle = leaf.boundary
        axis.add_patch(
            PlotRectangle(
                (rectangle.xmin, rectangle.ymin),
                rectangle.xmax - rectangle.xmin,
                rectangle.ymax - rectangle.ymin,
                fill=False,
                edgecolor=colormap(leaf.depth / max_depth),
                linewidth=0.65,
                alpha=0.95,
            )
        )
    axis.set(
        title=(
            "Partición completa del Quadtree "
            f"(capacidad por hoja: {tree.capacity})"
        ),
        xlabel="x (m)",
        ylabel="y (m)",
        xlim=(0, 10_000),
        ylim=(0, 10_000),
    )
    axis.set_aspect("equal")
    scalar_map = plt.cm.ScalarMappable(
        cmap=colormap, norm=plt.Normalize(vmin=0, vmax=max_depth)
    )
    scalar_map.set_array([])
    colorbar = fig.colorbar(scalar_map, ax=axis, pad=0.02)
    colorbar.set_label("Profundidad del nodo")
    fig.tight_layout()
    fig.savefig(ROOT / "divisiones_quadtree.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    unittest.main(exit=False)
    seed_text = os.environ.get("QUADTREE_SEED")
    seed = int(seed_text) if seed_text is not None else None
    create_visualizations(seed)
    print(
        "Visualizaciones creadas: radio_vecinos.png, "
        "vecino_mas_cercano.png, divisiones_quadtree.png"
    )
