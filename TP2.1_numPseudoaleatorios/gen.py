import argparse
import csv
import json
import math
import random
from pathlib import Path

import numpy as np
from scipy import stats


def gcl_generate(seed, a, c, m, n):
	x = seed % m
	seen = {x}
	states = []
	u_values = []
	cycle_detected = False
	stopped_reason = "n_alcanzado"

	for _ in range(n):
		x_next = (a * x + c) % m
		if x_next in seen:
			cycle_detected = True
			stopped_reason = "ciclo"
			break
		seen.add(x_next)
		states.append(x_next)
		u_values.append(x_next / m)
		x = x_next

	return {
		"name": "GCL",
		"seed": seed,
		"params": {"a": a, "c": c, "m": m},
		"states": states,
		"u": u_values,
		"n_generated": len(u_values),
		"stopped_reason": stopped_reason,
		"cycle_detected": cycle_detected,
	}


def middle_square_generate(seed, digits, n):
	base = 10 ** digits
	x = seed % base
	seen = {x}
	states = []
	u_values = []
	cycle_detected = False
	stopped_reason = "n_alcanzado"

	for _ in range(n):
		square = x * x
		width = 2 * digits
		square_str = str(square).zfill(width)
		start = (width - digits) // 2
		mid = square_str[start : start + digits]
		x_next = int(mid)

		if x_next == 0:
			states.append(x_next)
			u_values.append(x_next / base)
			stopped_reason = "degeneracion_cero"
			break
		if x_next in seen:
			cycle_detected = True
			stopped_reason = "ciclo"
			break

		seen.add(x_next)
		states.append(x_next)
		u_values.append(x_next / base)
		x = x_next

	return {
		"name": "CuadradosMedios",
		"seed": seed,
		"params": {"digitos": digits},
		"states": states,
		"u": u_values,
		"n_generated": len(u_values),
		"stopped_reason": stopped_reason,
		"cycle_detected": cycle_detected,
	}


def python_random_generate(seed, n):
	rng = random.Random(seed)
	u_values = [rng.random() for _ in range(n)]
	return {
		"name": "PythonRandom",
		"seed": seed,
		"params": {},
		"states": [],
		"u": u_values,
		"n_generated": len(u_values),
		"stopped_reason": "n_alcanzado",
		"cycle_detected": False,
	}


def chi_square_uniform(u_values, bins):
	if len(u_values) < bins or bins <= 1:
		return None
	counts, _ = np.histogram(u_values, bins=bins, range=(0.0, 1.0))
	expected = np.full(bins, len(u_values) / bins)
	stat, p_value = stats.chisquare(counts, expected)
	return stat, p_value


def ks_uniform(u_values):
	if len(u_values) < 2:
		return None
	stat, p_value = stats.kstest(u_values, "uniform")
	return stat, p_value


def runs_test(u_values):
	if len(u_values) < 2:
		return None
	median = 0.5
	runs = 1
	n1 = 0
	n2 = 0
	last = u_values[0] >= median
	if last:
		n1 += 1
	else:
		n2 += 1

	for value in u_values[1:]:
		current = value >= median
		if current != last:
			runs += 1
		last = current
		if current:
			n1 += 1
		else:
			n2 += 1

	if n1 == 0 or n2 == 0:
		return None

	mean = (2 * n1 * n2) / (n1 + n2) + 1
	var = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / (
		((n1 + n2) ** 2) * (n1 + n2 - 1)
	)
	z = (runs - mean) / math.sqrt(var)
	p_value = 2 * (1 - stats.norm.cdf(abs(z)))
	return z, p_value


def autocorr_test(u_values, lag):
	if len(u_values) <= lag or lag <= 0:
		return None
	x = np.array(u_values, dtype=float)
	x0 = x[:-lag]
	x1 = x[lag:]
	if x0.size < 2:
		return None
	r = np.corrcoef(x0, x1)[0, 1]
	if np.isnan(r):
		return None
	n = len(x0)
	z = r * math.sqrt(n)
	p_value = 2 * (1 - stats.norm.cdf(abs(z)))
	return r, p_value


NOMBRES_TEST = {
	"chi_square": "Chi-cuadrado",
	"ks":         "Kolmogorov-Smirnov",
	"runs":       "Corridas",
	"autocorr":   "Autocorrelacion",
}

NOMBRES_RAZON = {
	"n_alcanzado":       "N alcanzado",
	"ciclo":             "Ciclo detectado",
	"degeneracion_cero": "Degeneracion (cero)",
}


def run_tests(u_values, alpha, bins, lag):
	tests = [
		("chi_square", lambda u: chi_square_uniform(u, bins)),
		("ks",         ks_uniform),
		("runs",       runs_test),
		("autocorr",   lambda u: autocorr_test(u, lag)),
	]
	results = []
	for name, func in tests:
		result = func(u_values)
		if result is None:
			results.append({
				"test":      name,
				"statistic": None,
				"p_value":   None,
				"decision":  "N/A",
			})
			continue
		stat, p_value = result
		decision = "OK" if p_value >= alpha else "ERROR"
		results.append({
			"test":      name,
			"statistic": float(stat),
			"p_value":   float(p_value),
			"decision":  decision,
		})
	return results


def print_separator(char="─", width=54):
	print(char * width)


def print_generator_summary(generator):
	print_separator("═")
	print(f"  Generador  : {generator['name']}")
	print(f"  Semilla    : {generator['seed']}")
	if generator['params']:
		params_str = "  ".join(f"{k}={v}" for k, v in generator['params'].items())
		print(f"  Parametros : {params_str}")
	print(f"  Generados  : {generator['n_generated']}")
	razon = NOMBRES_RAZON.get(generator['stopped_reason'], generator['stopped_reason'])
	print(f"  Corte      : {razon}")
	if generator['cycle_detected']:
		print(f"Ciclo detectado en la secuencia")
	print_separator("─")


def print_test_table(test_results):
	col_test  = 22
	col_stat  = 13
	col_pval  = 13
	col_dec   = 10
	header = (
		f"{'Prueba':<{col_test}}"
		f"{'Estadistico':>{col_stat}}"
		f"{'p-valor':>{col_pval}}"
		f"{'Decision':>{col_dec}}"
	)
	print(header)
	print_separator("·", len(header))
	for row in test_results:
		nombre = NOMBRES_TEST.get(row['test'], row['test'])
		stat   = "N/A" if row['statistic'] is None else f"{row['statistic']:.6g}"
		pval   = "N/A" if row['p_value']   is None else f"{row['p_value']:.6g}"
		dec    = row['decision']
		print(
			f"{nombre:<{col_test}}"
			f"{stat:>{col_stat}}"
			f"{pval:>{col_pval}}"
			f"{dec:>{col_dec}}"
		)


def write_csv(rows, path):
	with path.open("w", newline="", encoding="utf-8") as file:
		writer = csv.DictWriter(
			file,
			fieldnames=["generador", "prueba", "estadistico", "p_valor", "decision"],
		)
		writer.writeheader()
		writer.writerows(rows)


def write_json(data, path):
	with path.open("w", encoding="utf-8") as file:
		json.dump(data, file, indent=2, ensure_ascii=False)


def build_cli():
	parser = argparse.ArgumentParser(
		description="TP2.1 — Generadores pseudoaleatorios y pruebas de calidad"
	)
	parser.add_argument("--n",             type=int,   default=10000,      help="Cantidad de valores a generar")
	parser.add_argument("--seed",          type=int,   default=12345,      help="Semilla para GCL y PythonRandom")
	parser.add_argument("--gcl-a",         type=int,   default=1103515245, help="Multiplicador a del GCL")
	parser.add_argument("--gcl-c",         type=int,   default=12345,      help="Incremento c del GCL")
	parser.add_argument("--gcl-m",         type=int,   default=2**31,      help="Modulo m del GCL")
	parser.add_argument("--ms-seed",       type=int,   default=None,       help="Semilla para cuadrados medios (opcional)")
	parser.add_argument("--ms-digits",     type=int,   default=4,          help="Digitos del estado en cuadrados medios")
	parser.add_argument("--alpha",         type=float, default=0.05,       help="Nivel de significancia alpha")
	parser.add_argument("--bins",          type=int,   default=10,         help="Intervalos para chi-cuadrado")
	parser.add_argument("--lag",           type=int,   default=1,          help="Lag para autocorrelacion")
	parser.add_argument(
		"--output-prefix",
		type=str,
		default="resultados/tp2_1_resultados",
		help="Prefijo para archivos de salida",
	)
	return parser


def main():
	parser = build_cli()
	args = parser.parse_args()

	if args.n <= 0:
		parser.error("n debe ser >= 1")
	if args.ms_digits <= 0:
		parser.error("ms-digits debe ser >= 1")
	if args.bins < 2:
		parser.error("bins debe ser >= 2")
	if args.lag < 1:
		parser.error("lag debe ser >= 1")

	ms_seed = args.ms_seed if args.ms_seed is not None else args.seed % (10 ** args.ms_digits)

	print(f"\nConfiguracion: n={args.n}  alpha={args.alpha}  bins={args.bins}  lag={args.lag}\n")

	generators = [
		gcl_generate(args.seed, args.gcl_a, args.gcl_c, args.gcl_m, args.n),
		middle_square_generate(ms_seed, args.ms_digits, args.n),
		python_random_generate(args.seed, args.n),
	]

	report   = {"config": {"n": args.n, "alpha": args.alpha, "bins": args.bins, "lag": args.lag}, "generadores": []}
	csv_rows = []

	for gen in generators:
		print_generator_summary(gen)
		test_results = run_tests(gen["u"], args.alpha, args.bins, args.lag)
		print_test_table(test_results)
		print()

		report["generadores"].append({
			"info": {
				"nombre":          gen["name"],
				"semilla":         gen["seed"],
				"parametros":      gen["params"],
				"n_generados":     gen["n_generated"],
				"razon_corte":     gen["stopped_reason"],
				"ciclo_detectado": gen["cycle_detected"],
			},
			"pruebas": test_results,
		})

		for row in test_results:
			csv_rows.append({
				"generador":   gen["name"],
				"prueba":      NOMBRES_TEST.get(row["test"], row["test"]),
				"estadistico": row["statistic"],
				"p_valor":     row["p_value"],
				"decision":    row["decision"],
			})

	output_prefix = Path(args.output_prefix)
	if not output_prefix.is_absolute():
		output_prefix = Path(__file__).resolve().parent / output_prefix
	output_prefix.parent.mkdir(parents=True, exist_ok=True)
	csv_path  = output_prefix.with_suffix(".csv")
	json_path = output_prefix.with_suffix(".json")
	write_csv(csv_rows, csv_path)
	write_json(report, json_path)

	print_separator("═")
	print(f"  Resultados exportados:")
	print(f"    CSV  → {csv_path}")
	print(f"    JSON → {json_path}")
	print_separator("═")


if __name__ == "__main__":
	main()