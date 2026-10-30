from __future__ import annotations

import statistics
import time
from pathlib import Path

from Quadtree import (
    Point,
    Rectangle,
    brute_force_nearest,
    brute_force_range,
    build_quadtree,
    generate_points,
)


def average_time(function, repetitions: int = 7) -> float:
    samples = []
    for _ in range(repetitions):
        start = time.perf_counter()
        function()
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def benchmark(sizes=(100, 500, 1_000, 2_500, 5_000, 10_000), queries=100) -> list[dict]:
    results = []
    for size in sizes:
        points = generate_points(size)
        boundary = Rectangle(0, 0, 10_000, 10_000)
        tree = build_quadtree(points, boundary)
        if size == 10_000:
            stats = tree.statistics()
            print(
                "\nEstructura para 10.000 puntos: "
                f"{stats['nodes']} nodos, {stats['leaves']} hojas, "
                f"profundidad máxima {stats['max_depth']}, "
                f"{stats['stored_points']} puntos almacenados, "
                f"máximo {stats['max_leaf_points']} puntos por hoja."
            )
        locations = [(i * 7919 % 10_000, i * 104729 % 10_000) for i in range(queries)]
        tree_range = average_time(
            lambda: [tree.range_search(x, y, 500) for x, y in locations]
        )
        brute_range = average_time(
            lambda: [brute_force_range(points, x, y, 500) for x, y in locations]
        )
        tree_nearest = average_time(
            lambda: [tree.nearest(x, y) for x, y in locations]
        )
        brute_nearest = average_time(
            lambda: [brute_force_nearest(points, x, y) for x, y in locations]
        )
        results.append({
            "n": size,
            "quadtree_range_ms": tree_range * 1000,
            "brute_range_ms": brute_range * 1000,
            "quadtree_nearest_ms": tree_nearest * 1000,
            "brute_nearest_ms": brute_nearest * 1000,
        })
    return results


def main() -> None:
    results = benchmark()
    print("n | range Quadtree (ms) | range fuerza bruta (ms) | nearest Quadtree (ms) | nearest fuerza bruta (ms)")
    print("-" * 105)
    for row in results:
        print(
            f"{row['n']:5d} | {row['quadtree_range_ms']:19.3f} | "
            f"{row['brute_range_ms']:24.3f} | {row['quadtree_nearest_ms']:21.3f} | "
            f"{row['brute_nearest_ms']:25.3f}"
        )
    crossover_range = next((r["n"] for r in results if r["quadtree_range_ms"] < r["brute_range_ms"]), None)
    crossover_nearest = next((r["n"] for r in results if r["quadtree_nearest_ms"] < r["brute_nearest_ms"]), None)
    print(f"\nPrimer tamaño medido donde gana range search: {crossover_range or 'no observado'}")
    print(f"Primer tamaño medido donde gana nearest: {crossover_nearest or 'no observado'}")
    print("\nLos tiempos dependen del hardware; el cruce debe reportarse con esta ejecución.")

    import matplotlib.pyplot as plt
    output = Path(__file__).parent / "benchmark.png"
    sizes = [r["n"] for r in results]
    plt.figure(figsize=(9, 5))
    for key, label in (
        ("quadtree_range_ms", "Quadtree range"),
        ("brute_range_ms", "Fuerza bruta range"),
        ("quadtree_nearest_ms", "Quadtree nearest"),
        ("brute_nearest_ms", "Fuerza bruta nearest"),
    ):
        plt.plot(sizes, [r[key] for r in results], marker="o", label=label)
    plt.xlabel("Número de puntos")
    plt.ylabel("Tiempo mediano para 100 consultas (ms)")
    plt.title("Comparación de rendimiento")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    print(f"Gráfica creada: {output.name}")


if __name__ == "__main__":
    main()
