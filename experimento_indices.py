
import csv
import os
import random
import statistics
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.setrecursionlimit(2000000)

from indice_binario import ABBTree
from estructura_bplus import BPlusTree
from datos_sinteticos import generate_students

CONFIG = {
    "BASE_SIZE": 1200,
    "SIZE_SCALES": list(range(4, 17)),
    "QUERY_COUNT": 1500,
    "REPETITIONS": 25,
    "RANGE_FRACTIONS": [0.02, 0.08, 0.15, 0.30],
    "LEAF_ORDER": 8,
    "RANDOM_SEED": 20261006,
    "OPERATION_BATCH": 40,
    "QUERY_BATCHES": [25, 100, 250, 750, 1500],
    "FIXED_QUERY_COUNT": 6000,
}



def filter_interval(records, lower_bound, upper_bound):
    return [structure for structure in records if lower_bound <= structure["id"] <= upper_bound]

def build_structures(records):
    abb_tree = ABBTree()
    bplus_tree = BPlusTree(t=CONFIG["LEAF_ORDER"])
    for structure in records:
        abb_tree.insert(structure)
        bplus_tree.insert(structure["id"], structure)
    return {"native_sequence": records, "binary_tree": abb_tree, "bplus_tree": bplus_tree}

def build_single(structure_name, records):
    if structure_name == "native_sequence":
        return records
    if structure_name == "binary_tree":
        abb_tree = ABBTree()
        for structure in records:
            abb_tree.insert(structure)
        return abb_tree
    bplus_tree = BPlusTree(t=CONFIG["LEAF_ORDER"])
    for structure in records:
        bplus_tree.insert(structure["id"], structure)
    return bplus_tree

def lookup_record(structure_name, records, record_id):
    if structure_name == "native_sequence":
        return next((structure for structure in records if structure["id"] == record_id), None)
    return records.search(record_id)

def query_interval(structure_name, records, lower_bound, upper_bound):
    if structure_name == "native_sequence":
        return filter_interval(records, lower_bound, upper_bound)
    return records.search_range(lower_bound, upper_bound)

def ordered_records(structure_name, records):
    if structure_name == "native_sequence":
        return sorted(records, key=lambda structure: structure["id"])
    return records.list_in_order()


STRUCTURE_KEYS = ["native_sequence", "binary_tree", "bplus_tree"]
INPUT_ORDERS = ["shuffled", "sorted"]

EXPERIMENTS = (
    ["lookup_only", "build_and_lookup"]
    + [f"interval_{int(fraction * 100)}pct" for fraction in CONFIG["RANGE_FRACTIONS"]]
    + ["ordered_scan"]
)

def select_bounds(ordered_ids, dataset_size, fraction):
    interval_size = max(1, int(dataset_size * fraction))
    start = min(dataset_size // 4, dataset_size - interval_size)
    lower_bound = ordered_ids[start]
    upper_bound = ordered_ids[start + interval_size - 1]
    return lower_bound, upper_bound, interval_size

def _summarize_timings(samples):
    if len(samples) >= 4:
        qs = statistics.quantiles(samples, n=4)
        p25, p75 = qs[0], qs[2]
    else:
        p25, p75 = min(samples), max(samples)
    return {
        "median": statistics.median(samples),
        "mean": statistics.fmean(samples),
        "stdev": statistics.stdev(samples) if len(samples) > 1 else 0.0,
        "min": min(samples),
        "max": max(samples),
        "p25": p25,
        "p75": p75,
        "raw": samples,
    }


def measure_once(operation):
    samples = []
    for _ in range(CONFIG["REPETITIONS"]):
        t0 = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - t0) / 1_000_000_000)
    return _summarize_timings(samples)


def measure_batch(operation, batch_size):
    samples = []
    for _ in range(CONFIG["REPETITIONS"]):
        t0 = time.perf_counter_ns()
        for _ in range(batch_size):
            operation()
        samples.append((time.perf_counter_ns() - t0) / batch_size / 1_000_000_000)
    return _summarize_timings(samples)


def run_scaling_experiment():
    base_size = CONFIG["BASE_SIZE"]
    dataset_sizes = [base_size * k for k in CONFIG["SIZE_SCALES"]]
    range_fractions = list(CONFIG["RANGE_FRACTIONS"])
    experiment_keys = (
        ["lookup_only", "build_and_lookup"]
        + [f"interval_{int(fraction * 100)}pct" for fraction in range_fractions]
        + ["ordered_scan"]
    )
    results = {(experiment_key, order_key, structure_key): [] for experiment_key in experiment_keys for order_key in INPUT_ORDERS for structure_key in STRUCTURE_KEYS}
    total_batches = len(dataset_sizes) * len(INPUT_ORDERS)
    current_batch = 0

    for size in dataset_sizes:
        for input_order in INPUT_ORDERS:
            current_batch += 1
            data_seed = CONFIG["RANDOM_SEED"] + size * 17 + (1 if input_order == "sorted" else 0)
            records = generate_students(size, sorted_input=(input_order == "sorted"), seed=data_seed)
            structures = build_structures(records)
            ids = [structure["id"] for structure in records]
            ordered_ids = sorted(ids)
            k_busq = min(CONFIG["QUERY_COUNT"], size)
            query_generator = random.Random(data_seed + 1)
            lookup_ids = query_generator.sample(ids, k_busq)
            input_label = "shuffled input" if input_order == "shuffled" else "sorted input"
            print(
                f"[{current_batch:02d}/{total_batches}] "
                f"conjunto={size:,} registros | entrada={input_label} | "
                f"consultas={k_busq:,}",
                flush=True,
            )

            bounds_by_fraction = {fraction: select_bounds(ordered_ids, size, fraction) for fraction in range_fractions}

            for structure_key in STRUCTURE_KEYS:
                structure = structures[structure_key]
                results[("lookup_only", input_order, structure_key)].append(
                    measure_once(lambda structure_key=structure_key, structure=structure: [lookup_record(structure_key, structure, i) for i in lookup_ids]))
                def _con(structure_key=structure_key):
                    built_structure = build_single(structure_key, records)
                    for i in lookup_ids:
                        lookup_record(structure_key, built_structure, i)
                results[("build_and_lookup", input_order, structure_key)].append(measure_once(_con))
                batch_size = CONFIG["OPERATION_BATCH"]
                for fraction in range_fractions:
                    lower_bound, upper_bound, _ = bounds_by_fraction[fraction]
                    key = f"interval_{int(fraction * 100)}pct"
                    results[(key, input_order, structure_key)].append(
                        measure_batch(lambda structure_key=structure_key, structure=structure, lower_bound=lower_bound, upper_bound=upper_bound: query_interval(structure_key, structure, lower_bound, upper_bound), batch_size))
                results[("ordered_scan", input_order, structure_key)].append(
                    measure_batch(lambda structure_key=structure_key, structure=structure: ordered_records(structure_key, structure), batch_size))

            for fraction in range_fractions:
                lower_bound, upper_bound, expected_count = bounds_by_fraction[fraction]
                row = [len(query_interval(structure_key, structures[structure_key], lower_bound, upper_bound)) for structure_key in STRUCTURE_KEYS]
                assert len(set(row)) == 1 and row[0] == expected_count, (fraction, row, expected_count)
            ordered_id_lists = [[record["id"] for record in ordered_records(structure_key, structures[structure_key])] for structure_key in STRUCTURE_KEYS]
            assert ordered_id_lists[0] == ordered_id_lists[1] == ordered_id_lists[2] == ordered_ids
    return dataset_sizes, results


def run_batch_experiment():
    fixed_size = CONFIG["FIXED_QUERY_COUNT"]
    batch_sizes = [query_count for query_count in CONFIG["QUERY_BATCHES"] if query_count <= fixed_size]
    assert batch_sizes, f"QUERY_BATCHES={CONFIG['QUERY_BATCHES']} all > fixed_size={fixed_size}"
    records = generate_students(fixed_size, sorted_input=False, seed=CONFIG["RANDOM_SEED"] + 991)
    structures = build_structures(records)
    ids = [structure["id"] for structure in records]
    batch_results = {structure_key: [] for structure_key in STRUCTURE_KEYS}
    for query_count in batch_sizes:
        batch_lookup_ids = random.Random(CONFIG["RANDOM_SEED"] + 1000 + query_count).sample(ids, query_count)
        print(
            f"[lote variable] universo fijo={fixed_size:,} | "
            f"consultas en bloque={query_count:,}",
            flush=True,
        )
        for structure_key in STRUCTURE_KEYS:
            structure = structures[structure_key]
            batch_results[structure_key].append(measure_once(lambda structure_key=structure_key, structure=structure: [lookup_record(structure_key, structure, i) for i in batch_lookup_ids]))
    return fixed_size, batch_sizes, batch_results


def experiment_title(experiment_key):

    nb = CONFIG["QUERY_COUNT"]
    if experiment_key == "lookup_only":
        return f"{nb} busquedas aleatorias por id (sin construccion)"
    if experiment_key == "build_and_lookup":
        return f"{nb} busquedas aleatorias por id (incluyendo construccion)"
    if experiment_key.startswith("interval_"):
        pct = experiment_key.replace("interval_", "").replace("pct", "")
        return f"Busqueda por rango ({pct}% de los ids)"
    if experiment_key == "ordered_scan":
        return "Complete ordered listing by id"
    return experiment_key

DISPLAY_NAMES = {
    "native_sequence": "Python sequence",
    "binary_tree": "Binary search tree",
    "bplus_tree": "B+ tree",
}

FILE_LABELS = {
    "lookup_only": "lookups_only",
    "build_and_lookup": "build_and_lookup",
    "interval_2pct": "range_02pct",
    "interval_8pct": "range_08pct",
    "interval_15pct": "range_15pct",
    "interval_30pct": "range_30pct",
    "ordered_scan": "ordered_scan",
}

STYLE_CONFIG = {
    "native_sequence": {"color": "#5B21B6", "marker": "o", "label": DISPLAY_NAMES["native_sequence"]},
    "binary_tree": {"color": "#E05A33", "marker": "s", "label": DISPLAY_NAMES["binary_tree"]},
    "bplus_tree": {"color": "#008C95", "marker": "^", "label": DISPLAY_NAMES["bplus_tree"]},
}


def _interquartile_error(ds):
    medians = [summary["median"] * 1000 for summary in ds]
    low, high = [], []
    for summary, query_count in zip(ds, medians):
        p25 = summary.get("p25", summary["median"]) * 1000
        p75 = summary.get("p75", summary["median"]) * 1000
        lower_bound = max(0.0, query_count - p25)
        upper_bound = max(0.0, p75 - query_count)
        if query_count > 0:
            lower_bound = min(lower_bound, query_count * 0.999)
        low.append(lower_bound)
        high.append(upper_bound)
    return medians, [low, high]


def _configure_log_axis(axis):
    from matplotlib.ticker import LogFormatterMathtext, LogLocator
    axis.set_yscale("log")
    axis.yaxis.set_major_locator(LogLocator(base=10, numticks=12))
    axis.yaxis.set_minor_locator(
        LogLocator(base=10, subs=tuple(float(i) for i in range(2, 10)), numticks=24))
    axis.yaxis.set_major_formatter(LogFormatterMathtext(base=10))


def _shared_y_limits(results, experiment_key, input_orders, margin=1.15):
    lower_bound, upper_bound = float("inf"), 0.0
    for order_key in input_orders:
        for structure_key in STRUCTURE_KEYS:
            for summary in results[(experiment_key, order_key, structure_key)]:
                p25 = summary.get("p25", summary["median"]) * 1000
                p75 = summary.get("p75", summary["median"]) * 1000
                if p25 > 0:
                    lower_bound = min(lower_bound, p25)
                if p75 > 0:
                    upper_bound = max(upper_bound, p75)
    if not upper_bound > 0:
        return None
    if not lower_bound > 0 or lower_bound >= upper_bound:
        lower_bound = upper_bound / 100.0
    return (lower_bound / margin, upper_bound * margin)


def plot_scaling(dataset_sizes, results):
    import math
    import os
    project_dir = _project_root()
    results_dir = os.path.join(project_dir, "Resultados")
    os.makedirs(results_dir, exist_ok=True)
    x_labels = [f"{k}n" for k in CONFIG["SIZE_SCALES"]]
    base_size = CONFIG["BASE_SIZE"]
    experiment_keys = list(results.keys())
    seen_experiments = []
    for (experiment_key, _o, _s) in experiment_keys:
        if experiment_key not in seen_experiments:
            seen_experiments.append(experiment_key)

    for experiment_key in seen_experiments:
        ylim = _shared_y_limits(results, experiment_key, INPUT_ORDERS)
        fig, axes = plt.subplots(2, 1, figsize=(11, 10), sharex=True, sharey=True)
        fig.patch.set_facecolor("#111827")
        for axis, input_order in zip(axes, INPUT_ORDERS):
            for structure_key in STRUCTURE_KEYS:
                style = STYLE_CONFIG[structure_key]
                medians, error_bars = _interquartile_error(results[(experiment_key, input_order, structure_key)])
                axis.errorbar(dataset_sizes, medians, yerr=error_bars, color=style["color"],
                            marker=style["marker"], linestyle="--", linewidth=2.0,
                            markersize=7, markeredgecolor="#FFFFFF",
                            markeredgewidth=0.7, capsize=4, elinewidth=1.2,
                            label=style["label"])
            axis.set_title(f"{input_order.title()} · {experiment_title(experiment_key)}", fontsize=13,
                         fontweight="bold", color="#F9FAFB")
            axis.set_xlabel("Relative dataset size (N)" if axis is axes[-1] else "",
                          color="#E5E7EB")
            axis.set_ylabel("Mediana (ms)" if axis is axes[0] else "", color="#E5E7EB")
            axis.set_xticks(dataset_sizes)
            axis.set_xticklabels(x_labels, rotation=45, ha="right")
            axis.set_xscale("log")
            _configure_log_axis(axis)
            if ylim is not None:
                axis.set_ylim(ylim)
            axis.set_facecolor("#1F2937")
            axis.tick_params(colors="#D1D5DB")
            axis.grid(alpha=0.28, which="major", color="#9CA3AF", linestyle=":")
            axis.grid(alpha=0.10, which="minor", color="#6B7280", linestyle=":")
            axis.legend(loc="upper left", frameon=True, facecolor="#111827",
                      edgecolor="#6B7280", labelcolor="#F9FAFB")
        fig.suptitle(f"{experiment_title(experiment_key)} · {CONFIG['REPETITIONS']} repetitions",
                     fontsize=16, fontweight="bold", color="#F9FAFB")
        fig.tight_layout()
        figure_name = FILE_LABELS.get(experiment_key, experiment_key)
        fig.savefig(os.path.join(results_dir, f"figura_{figure_name}.png"), dpi=160)
        plt.close(fig)

    summary_keys = ["lookup_only", "build_and_lookup",
                      "interval_10pct" if "interval_10pct" in seen_experiments else seen_experiments[2],
                      "ordered_scan"]
    fig, axes = plt.subplots(4, 2, figsize=(13, 14))
    fig.patch.set_facecolor("#111827")
    for row, experiment_key in enumerate(summary_keys):
        ylim = _shared_y_limits(results, experiment_key, INPUT_ORDERS)
        for column, input_order in enumerate(INPUT_ORDERS):
            axis = axes[row][column]
            _draw_summary_panel(axis, experiment_key, input_order, dataset_sizes, results, x_labels, scale="log")
            if ylim is not None:
                axis.set_ylim(ylim)
    fig.tight_layout()
    fig.savefig(os.path.join(results_dir, "panel_comparativo_loglog.png"), dpi=160,
                facecolor=fig.get_facecolor())
    plt.close(fig)


def _draw_summary_panel(axis, experiment_key, input_order, dataset_sizes, results, x_labels, scale="log"):
    import math
    for structure_key in STRUCTURE_KEYS:
        style = STYLE_CONFIG[structure_key]
        medians, error_bars = _interquartile_error(results[(experiment_key, input_order, structure_key)])
        axis.errorbar(dataset_sizes, medians, yerr=error_bars, color=style["color"],
                    marker=style["marker"], linestyle="--", label=style["label"],
                    lw=1.8, markersize=5, markeredgecolor="#FFFFFF",
                    markeredgewidth=0.5, capsize=2, elinewidth=1)
    if experiment_key == "lookup_only":
        meds_lista = [summary["median"] * 1000 for summary in results[(experiment_key, input_order, "native_sequence")]]
        n0, y0 = dataset_sizes[0], meds_lista[0]
        if y0 > 0 and n0 > 1:
            axis.plot(dataset_sizes, [y0 * (size / n0) for size in dataset_sizes],
                    color="#D1D5DB", linestyle="--", alpha=0.55, label="O(N) referencia")
            axis.plot(dataset_sizes, [y0 * (math.log(size) / math.log(n0)) for size in dataset_sizes],
                    color="#9CA3AF", linestyle=":", alpha=0.65, label="O(log N) referencia")
    axis.set_title(f"{experiment_title(experiment_key)} · {input_order.title()}", fontsize=10, color="#F9FAFB")
    axis.set_xticks(dataset_sizes)
    axis.set_xticklabels(x_labels, rotation=45, ha="right")
    axis.set_ylabel("ms (mediana+IQR)", color="#E5E7EB")
    axis.tick_params(colors="#D1D5DB")
    axis.set_xscale("log")
    if scale == "log":
        _configure_log_axis(axis)
    axis.grid(alpha=0.28, which="major", color="#9CA3AF", linestyle=":")
    axis.grid(alpha=0.10, which="minor", color="#6B7280", linestyle=":")
    axis.set_facecolor("#1F2937")
    axis.legend(fontsize=8, frameon=True, facecolor="#111827",
              edgecolor="#6B7280", labelcolor="#F9FAFB")


def plot_linear_summary(dataset_sizes, results):
    project_dir = _project_root()
    results_dir = os.path.join(project_dir, "Resultados")
    os.makedirs(results_dir, exist_ok=True)
    x_labels = [f"{k}n" for k in CONFIG["SIZE_SCALES"]]
    seen_experiments = []
    for (experiment_key, _o, _s) in results:
        if experiment_key not in seen_experiments:
            seen_experiments.append(experiment_key)
    summary_keys = ["lookup_only", "build_and_lookup",
              "interval_10pct" if "interval_10pct" in seen_experiments else seen_experiments[2],
              "ordered_scan"]
    fig, axes = plt.subplots(4, 2, figsize=(13, 14))
    fig.patch.set_facecolor("#111827")
    for row, experiment_key in enumerate(summary_keys):
        for column, input_order in enumerate(INPUT_ORDERS):
            _draw_summary_panel(axes[row][column], experiment_key, input_order, dataset_sizes, results, x_labels, scale="semilog")
    fig.suptitle(f"Semi-log panel — median of {CONFIG['REPETITIONS']} repetitions",
                 fontsize=14, fontweight="bold", color="#F9FAFB")
    fig.tight_layout()
    output_path = os.path.join(results_dir, "panel_comparativo_semilog.png")
    fig.savefig(output_path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Semi-log summary at: {output_path}")


def plot_batch_times(fixed_size, batch_sizes, batch_results):
    import os
    project_dir = _project_root()
    results_dir = os.path.join(project_dir, "Resultados")
    os.makedirs(results_dir, exist_ok=True)
    fig, axis = plt.subplots(figsize=(10.5, 6.5), dpi=160)
    fig.patch.set_facecolor("#0B132B")
    axis.set_facecolor("#1C2541")
    for structure_key in STRUCTURE_KEYS:
        style = STYLE_CONFIG[structure_key]
        medians, error_bars = _interquartile_error(batch_results[structure_key])
        axis.errorbar(batch_sizes, medians, yerr=error_bars, color=style["color"],
                    marker=style["marker"], linestyle="-.", label=style["label"],
                    lw=2.4, markersize=8, markeredgecolor="#F8FAFC",
                    markeredgewidth=0.7, capsize=4, elinewidth=1.3)
    axis.set_title(f"Presupuesto temporal del lote · universo fijo {fixed_size:,}",
                 fontsize=15, fontweight="bold", color="#F8FAFC", pad=14)
    axis.set_xlabel("Number of queries in batch", color="#D9E2EC")
    axis.set_ylabel("Median batch duration (ms)", color="#D9E2EC")
    axis.set_xscale("log")
    _configure_log_axis(axis)
    axis.set_xticks(batch_sizes)
    axis.set_xticklabels([str(query_count) for query_count in batch_sizes])
    axis.tick_params(colors="#D9E2EC")
    axis.grid(alpha=0.30, which="major", color="#8FA3BF", linestyle=":")
    axis.grid(alpha=0.12, which="minor", color="#8FA3BF", linestyle=":")
    axis.legend(frameon=True, facecolor="#0B132B", edgecolor="#5BC0BE",
              labelcolor="#F8FAFC", loc="upper left")
    fig.tight_layout()
    output_path = os.path.join(results_dir, "figura_consultas_por_lote.png")
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    print(f"Batch-size chart at: {output_path}")
    for structure_key in STRUCTURE_KEYS:
        medians = [f"{summary['median'] * 1000:.3f}" for summary in batch_results[structure_key]]
        print(f"  {DISPLAY_NAMES[structure_key]:18s} M={batch_sizes} -> ms=[{', '.join(medians)}]")


def plot_per_query_cost(fixed_size, batch_sizes, batch_results):
    import os
    project_dir = _project_root()
    output_dir = os.path.join(project_dir, "Resultados")
    os.makedirs(output_dir, exist_ok=True)
    fig, axis = plt.subplots(figsize=(10.5, 6.5), dpi=160)
    fig.patch.set_facecolor("#201A30")
    axis.set_facecolor("#332A4A")
    for structure_key in STRUCTURE_KEYS:
        style = STYLE_CONFIG[structure_key]
        unitarios = [datos["median"] * 1000 / query_count for datos, query_count in zip(batch_results[structure_key], batch_sizes)]
        axis.plot(batch_sizes, unitarios, color=style["color"], marker=style["marker"],
                linewidth=2.4, markersize=8, markeredgecolor="#FFF7ED",
                markeredgewidth=0.7, linestyle=":", label=style["label"])
    axis.set_title(f"Huella media por consulta · conjunto de {fixed_size:,} elementos",
                 fontsize=15, fontweight="bold", color="#FFF7ED", pad=14)
    axis.set_xlabel("Accumulated queries in batch", color="#F3E8FF")
    axis.set_ylabel("Tiempo unitario (ms / consulta)", color="#F3E8FF")
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xticks(batch_sizes)
    axis.set_xticklabels([str(query_count) for query_count in batch_sizes])
    axis.tick_params(colors="#F3E8FF")
    axis.grid(alpha=0.30, which="major", color="#C4B5FD", linestyle="--")
    axis.grid(alpha=0.12, which="minor", color="#C4B5FD", linestyle=":")
    axis.legend(frameon=True, facecolor="#201A30", edgecolor="#F59E0B",
              labelcolor="#FFF7ED", loc="best")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "figura_huella_por_consulta.png"), dpi=180,
                facecolor=fig.get_facecolor())
    plt.close(fig)


def _project_root():
    import os
    cwd = os.getcwd()
    if os.path.basename(cwd) == "Lab 3" and os.path.isfile(os.path.join(cwd, "experimento_indices.py")):
        return cwd
    candidato = os.path.join(cwd, "Lab 3")
    if os.path.isdir(candidato):
        return candidato
    return os.path.dirname(os.path.abspath(__file__))


def write_results(dataset_sizes, results):
    import os
    project_dir = _project_root()
    results_dir = os.path.join(project_dir, "Resultados")
    sampling_dir = os.path.join(project_dir, "Muestreo_estadistico")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(sampling_dir, exist_ok=True)
    with open(os.path.join(results_dir, "mediciones_resumen.csv"), "w",
              newline="", encoding="utf-8") as fraction:
        writer = csv.writer(fraction)
        k0, k1 = CONFIG["SIZE_SCALES"][0], CONFIG["SIZE_SCALES"][-1]
        writer.writerow(["prueba", "descripcion", "input_order", "indice"]
                   + [f"N={size}_median_ms" for size in dataset_sizes]
                   + [f"N={size}_stdev_ms" for size in dataset_sizes]
                   + [f"factor_{k1}n/{k0}n_medianas"])
        for experiment_key in sorted({k[0] for k in results}):
            for order_key in INPUT_ORDERS:
                for structure_key in STRUCTURE_KEYS:
                    samples = results[(experiment_key, order_key, structure_key)]
                    medians = [f"{summary['median'] * 1000:.4f}" for summary in samples]
                    stds = [f"{summary['stdev'] * 1000:.4f}" for summary in samples]
                    factor = f"{samples[-1]['median'] / samples[0]['median']:.2f}" if samples[0]["median"] > 0 else "inf"
                    writer.writerow([experiment_key, experiment_title(experiment_key), order_key, DISPLAY_NAMES[structure_key]] + medians + stds + [factor])
    with open(os.path.join(results_dir, "mediciones_detalladas.csv"), "w",
              newline="", encoding="utf-8") as fraction:
        writer = csv.writer(fraction)
        writer.writerow(["prueba", "input_order", "indice", "size_N",
                    "mediana_ms", "promedio_ms", "desviacion_ms", "minimo_ms", "maximo_ms"])
        for experiment_key in sorted({k[0] for k in results}):
            for order_key in INPUT_ORDERS:
                for structure_key in STRUCTURE_KEYS:
                    for size, summary in zip(dataset_sizes, results[(experiment_key, order_key, structure_key)]):
                        writer.writerow([experiment_key, order_key, DISPLAY_NAMES[structure_key], size,
                                    f"{summary['median'] * 1000:.4f}", f"{summary['mean'] * 1000:.4f}",
                                    f"{summary['stdev'] * 1000:.4f}", f"{summary['min'] * 1000:.4f}",
                                    f"{summary['max'] * 1000:.4f}"])
    with open(os.path.join(sampling_dir, "muestras_crudas.csv"), "w",
              newline="", encoding="utf-8") as fraction:
        writer = csv.writer(fraction)
        writer.writerow(["prueba", "input_order", "indice", "size_N", "muestra", "duration_ms"])
        for experiment_key in sorted({k[0] for k in results}):
            for order_key in INPUT_ORDERS:
                for structure_key in STRUCTURE_KEYS:
                    for size, summary in zip(dataset_sizes, results[(experiment_key, order_key, structure_key)]):
                        for sample_number, t in enumerate(summary.get("raw", [])):
                            writer.writerow([experiment_key, order_key, DISPLAY_NAMES[structure_key], size, sample_number + 1, f"{t * 1000:.6f}"])
    print("Export complete: Resultados/ y Muestreo_estadistico/")


def print_summary(dataset_sizes, results):
    k0, k1 = CONFIG["SIZE_SCALES"][0], CONFIG["SIZE_SCALES"][-1]
    print("\n" + "=" * 68)
    print(f"SCALABILITY SUMMARY · comparison {k0}n → {k1}n")
    print("Relative median factor and observed dispersion")
    print("-" * 68)
    for experiment_key in sorted({k[0] for k in results}):
        for order_key in INPUT_ORDERS:
            for structure_key in STRUCTURE_KEYS:
                samples = results[(experiment_key, order_key, structure_key)]
                factor = samples[-1]["median"] / samples[0]["median"] if samples[0]["median"] > 0 else float("inf")
                print(
                    f"{FILE_LABELS.get(experiment_key, experiment_key):24s} | "
                    f"{'mezclada' if order_key == 'shuffled' else 'creciente':10s} | "
                    f"{DISPLAY_NAMES[structure_key]:18s} | "
                    f"index x{factor:6.2f} | "
                    f"final {samples[-1]['median'] * 1000:9.2f} ms | "
                    f"variation {samples[-1]['stdev'] * 1000:7.2f} ms"
                )
    print("=" * 68)


if __name__ == "__main__":
    print("=" * 68)
    print("BENCHMARK START")
    print("Robust measurements with median and interquartile range")
    print("-" * 68)
    print(
        f"Evaluated scales: {len(CONFIG['SIZE_SCALES'])} sizes | "
        f"repetitions per point: {CONFIG['REPETITIONS']}"
    )
    print(
        f"Queries per scenario: {CONFIG['QUERY_COUNT']} | "
        f"batch for ranges/listings: {CONFIG['OPERATION_BATCH']}"
    )
    print(
        f"Fracciones de intervalo: "
        f"{', '.join(f'{int(fraction * 100)}%' for fraction in CONFIG['RANGE_FRACTIONS'])}"
    )
    print(f"Reproducible seed: {CONFIG['RANDOM_SEED']}")
    print("-" * 68)
    inicio_total = time.perf_counter()
    dataset_sizes, results = run_scaling_experiment()
    write_results(dataset_sizes, results)
    plot_scaling(dataset_sizes, results)
    plot_linear_summary(dataset_sizes, results)
    fixed_size, batch_sizes, batch_results = run_batch_experiment()
    plot_batch_times(fixed_size, batch_sizes, batch_results)
    plot_per_query_cost(fixed_size, batch_sizes, batch_results)
    print_summary(dataset_sizes, results)
    fin_total = time.perf_counter()
    print("-" * 68)
    print(f"BENCHMARK FINISHED | total duration: {fin_total - inicio_total:.2f} s")
