import argparse
import csv
from collections import defaultdict
from pathlib import Path


def group_samples(file):
    groups = defaultdict(list)
    with file.open(newline="", encoding="utf-8-sig") as input_file:
        for row in csv.DictReader(input_file):
            identifier = (
                row["prueba"],
                row["input_order"],
                row["indice"],
                int(row["size_N"]),
            )
            groups[identifier].append(float(row["duration_ms"]))
    return groups


def evaluate_group(values, threshold):
    if len(values) < 3 or len(set(values)) < 2:
        return "", "not evaluable"
    from scipy.stats import shapiro
    try:
        statistic, probability = shapiro(values)
    except ValueError:
        return "", "not evaluable"
    decision = "compatible" if probability >= threshold else "not compatible"
    return f"{probability:.6g}", decision


def analyze(input_file, output_file, threshold):
    groups = group_samples(input_file)
    rows = []
    for key in sorted(groups, key=lambda elemento: (elemento[0], elemento[1], elemento[2], elemento[3])):
        p_value, decision = evaluate_group(groups[key], threshold)
        rows.append((*key, len(groups[key]), p_value, decision))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as output_stream:
        writer = csv.writer(output_stream)
        writer.writerow(["prueba", "input_order", "indice", "size_N",
                         "muestras", "p_value", "resultado"])
        writer.writerows(rows)
    return rows


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Evaluate the distribution of timing samples")
    parser.add_argument("--raw", type=Path,
                        default=folder / "Muestreo_estadistico" / "muestras_crudas.csv")
    parser.add_argument("--out", type=Path,
                        default=folder / "Muestreo_estadistico" / "evaluacion_normalidad.csv")
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    results = analyze(args.raw, args.out, args.alpha)
    valid_groups = [row for row in results if row[-1] in ("compatible", "not compatible")]
    rejected = sum(row[-1] == "not compatible" for row in valid_groups)
    print(f"Groups analyzed: {len(results)}")
    print(f"Evaluable groups: {len(valid_groups)}")
    print(f"Rejections with alpha={args.alpha}: {rejected}")
    print(f"Generated file: {args.out}")


if __name__ == "__main__":
    main()
