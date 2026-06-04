import argparse
import csv
import json
import math
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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


COLORES = ["#2196F3", "#F44336", "#4CAF50"]


def plot_generators(generators, output_prefix):
	"""Genera 3 gráficas comparativas y las guarda como PNG."""
	names  = [g["name"]        for g in generators]
	u_vals = [g["u"]           for g in generators]

	# ── 1. Histogramas de distribución ───────────────────────────
	fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)
	fig.suptitle("Distribución de valores generados (histograma)", fontsize=13)
	for ax, name, u, color in zip(axes, names, u_vals, COLORES):
		if len(u) == 0:
			ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
		else:
			ax.hist(u, bins=20, range=(0, 1), color=color, edgecolor="white", alpha=0.85)
			ax.axhline(len(u) / 20, color="black", linestyle="--", linewidth=1, label="Esperado")
			ax.legend(fontsize=8)
		ax.set_title(name, fontsize=11)
		ax.set_xlabel("Valor u")
		ax.set_ylabel("Frecuencia")
		ax.set_xlim(0, 1)
	plt.tight_layout()
	path_hist = output_prefix.parent / (output_prefix.name + "_histogramas.png")
	fig.savefig(path_hist, dpi=150)
	plt.close(fig)

	# ── 2. Dispersión u_i vs u_{i+1} (detección de patrones) ─────
	fig, axes = plt.subplots(1, 3, figsize=(15, 5))
	fig.suptitle("Dispersión u_i vs u_{i+1} (correlación sucesiva)", fontsize=13)
	for ax, name, u, color in zip(axes, names, u_vals, COLORES):
		if len(u) < 2:
			ax.text(0.5, 0.5, "Insuficientes datos", ha="center", va="center")
		else:
			max_pts = min(len(u) - 1, 5000)
			ax.scatter(u[:max_pts], u[1:max_pts+1],
					   s=1.5, alpha=0.35, color=color)
		ax.set_title(name, fontsize=11)
		ax.set_xlabel("u_i")
		ax.set_ylabel("u_{i+1}")
		ax.set_xlim(0, 1)
		ax.set_ylim(0, 1)
	plt.tight_layout()
	path_scatter = output_prefix.parent / (output_prefix.name + "_dispersion.png")
	fig.savefig(path_scatter, dpi=150)
	plt.close(fig)

	# ── 3. Serie temporal (primeros 200 valores) ─────────────────
	fig, ax = plt.subplots(figsize=(14, 4))
	fig.suptitle("Serie temporal — primeros 200 valores generados", fontsize=13)
	for name, u, color in zip(names, u_vals, COLORES):
		n = min(len(u), 200)
		if n == 0:
			continue
		ax.plot(range(n), u[:n], color=color, linewidth=0.8,
				marker="o", markersize=2, alpha=0.7, label=name)
	ax.axhline(0.5, color="black", linestyle="--", linewidth=0.8, label="Media teórica")
	ax.set_xlabel("Índice")
	ax.set_ylabel("Valor u")
	ax.set_ylim(-0.05, 1.05)
	ax.legend(fontsize=9)
	plt.tight_layout()
	path_series = output_prefix.parent / (output_prefix.name + "_serie_temporal.png")
	fig.savefig(path_series, dpi=150)
	plt.close(fig)

	return path_hist, path_scatter, path_series


def plot_pvalues(generators, test_results_map, alpha, output_prefix):
	"""Gráfica de barras agrupadas: p-valor por test y generador."""
	test_keys = ["chi_square", "ks", "runs", "autocorr"]
	test_labels = [NOMBRES_TEST[k] for k in test_keys]
	names = [g["name"] for g in generators]

	x = np.arange(len(test_keys))
	width = 0.22
	fig, ax = plt.subplots(figsize=(12, 5))
	for i, (name, color) in enumerate(zip(names, COLORES)):
		pvals = []
		for tk in test_keys:
			row = next((r for r in test_results_map[name] if r["test"] == tk), None)
			pvals.append(row["p_value"] if row and row["p_value"] is not None else 0.0)
		offset = (i - 1) * width
		bars = ax.bar(x + offset, pvals, width, label=name, color=color, alpha=0.85, edgecolor="white")
		for bar, pv in zip(bars, pvals):
			if pv is not None:
				ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
						f"{pv:.2f}", ha="center", va="bottom", fontsize=7)
	ax.axhline(alpha, color="red", linestyle="--", linewidth=1.2, label=f"\u03b1 = {alpha}")
	ax.set_xticks(x)
	ax.set_xticklabels(test_labels, fontsize=10)
	ax.set_ylabel("p-valor")
	ax.set_ylim(0, 1.12)
	ax.set_title("P-valores por test y generador", fontsize=13)
	ax.legend(fontsize=9)
	plt.tight_layout()
	path_pval = output_prefix.parent / (output_prefix.name + "_pvalores.png")
	fig.savefig(path_pval, dpi=150)
	plt.close(fig)
	return path_pval


def plot_acf(generators, max_lag, output_prefix):
	"""Función de autocorrelación (ACF) para múltiples lags."""
	fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
	fig.suptitle(f"Autocorrelación (ACF) — lags 1–{max_lag}", fontsize=13)
	for ax, gen, color in zip(axes, generators, COLORES):
		u = np.array(gen["u"], dtype=float)
		lags = range(1, max_lag + 1)
		rs = []
		for lag in lags:
			if len(u) > lag:
				r = np.corrcoef(u[:-lag], u[lag:])[0, 1]
				rs.append(r if not np.isnan(r) else 0.0)
			else:
				rs.append(0.0)
		conf = 1.96 / np.sqrt(max(len(u), 1))
		ax.bar(list(lags), rs, color=color, alpha=0.8, edgecolor="white")
		ax.axhline( conf, color="red",  linestyle="--", linewidth=1, label="\u00b195% IC")
		ax.axhline(-conf, color="red",  linestyle="--", linewidth=1)
		ax.axhline(0,     color="black", linestyle="-",  linewidth=0.5)
		ax.set_title(gen["name"], fontsize=11)
		ax.set_xlabel("Lag")
		ax.set_ylabel("Autocorrelación")
		ax.legend(fontsize=8)
	plt.tight_layout()
	path_acf = output_prefix.parent / (output_prefix.name + "_acf.png")
	fig.savefig(path_acf, dpi=150)
	plt.close(fig)
	return path_acf


def plot_qq(generators, output_prefix):
	"""Q-Q plot de valores generados vs. distribución uniforme teórica."""
	fig, axes = plt.subplots(1, 3, figsize=(15, 5))
	fig.suptitle("Q-Q plot: cuantiles empíricos vs. Uniforme(0,1)", fontsize=13)
	for ax, gen, color in zip(axes, generators, COLORES):
		u = np.sort(gen["u"])
		n = len(u)
		if n < 2:
			ax.text(0.5, 0.5, "Insuficientes datos", ha="center", va="center")
		else:
			theoretical = np.linspace(0, 1, n)
			ax.scatter(theoretical, u, s=2, alpha=0.4, color=color)
			ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Línea ideal")
			ax.legend(fontsize=8)
		ax.set_title(gen["name"], fontsize=11)
		ax.set_xlabel("Cuantiles teóricos")
		ax.set_ylabel("Cuantiles empíricos")
		ax.set_xlim(0, 1)
		ax.set_ylim(0, 1)
	plt.tight_layout()
	path_qq = output_prefix.parent / (output_prefix.name + "_qq.png")
	fig.savefig(path_qq, dpi=150)
	plt.close(fig)
	return path_qq


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
	all_test_results = {}

	for gen in generators:
		print_generator_summary(gen)
		test_results = run_tests(gen["u"], args.alpha, args.bins, args.lag)
		all_test_results[gen["name"]] = test_results
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

	test_results_map = all_test_results

	path_hist, path_scatter, path_series = plot_generators(generators, output_prefix)
	path_pval = plot_pvalues(generators, test_results_map, args.alpha, output_prefix)
	path_acf  = plot_acf(generators, max_lag=20, output_prefix=output_prefix)
	path_qq   = plot_qq(generators, output_prefix)

	print_separator("═")
	print(f"  Resultados exportados:")
	print(f"    CSV  → {csv_path}")
	print(f"    JSON → {json_path}")
	for p in [path_hist, path_scatter, path_series, path_pval, path_acf, path_qq]:
		print(f"    PNG  → {p.name}")
	print_separator("═")


if __name__ == "__main__":
	main()