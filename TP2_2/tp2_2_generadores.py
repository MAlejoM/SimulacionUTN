import argparse
import json
import os
import math
import random
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from collections import Counter

# =====================================================================
# TP2.2 - Generadores de numeros pseudoaleatorios
# =====================================================================

# ---------- Generador Uniforme Base (GCL) ----------

class GeneradorUniforme:
    def __init__(self, metodo="GCL", seed=42, a=1664525, c=1013904223, m=2**32):
        self.metodo = metodo
        self.seed = seed
        self.a = a
        self.c = c
        self.m = m
        self.current_x = seed % m
        self.rng = random.Random(seed)

    def next_u(self):
        if self.metodo == "GCL":
            self.current_x = (self.a * self.current_x + self.c) % self.m
            return self.current_x / self.m
        return self.rng.random()

# ---------- Generadores por distribucion ----------

def gen_uniforme(generador_u, a, b, n):
    muestras = []
    for _ in range(n):
        u = generador_u.next_u()
        muestras.append(a + u * (b - a))
    return muestras

def gen_exponencial(generador_u, lam, n):
    muestras = []
    for _ in range(n):
        u = generador_u.next_u()
        while u <= 1e-10:
            u = generador_u.next_u()
        muestras.append(-math.log(u) / lam)
    return muestras

def gen_gamma_entera(generador_u, k, lam, n):
    muestras = []
    for _ in range(n):
        suma = 0.0
        for _ in range(k):
            u = generador_u.next_u()
            while u <= 1e-10:
                u = generador_u.next_u()
            suma += -math.log(u) / lam
        muestras.append(suma)
    return muestras

def gen_normal(generador_u, mu, sigma, n):
    muestras = []
    guardado = None
    while len(muestras) < n:
        if guardado is not None:
            muestras.append(mu + guardado * sigma)
            guardado = None
            continue
        u1 = generador_u.next_u()
        u2 = generador_u.next_u()
        while u1 <= 1e-10:
            u1 = generador_u.next_u()
        r = math.sqrt(-2.0 * math.log(u1))
        z0 = r * math.cos(2.0 * math.pi * u2)
        z1 = r * math.sin(2.0 * math.pi * u2)
        muestras.append(mu + z0 * sigma)
        guardado = z1
    return muestras[:n]

def gen_normal_polar(generador_u, mu, sigma, n):
    muestras = []
    guardado = None
    while len(muestras) < n:
        if guardado is not None:
            muestras.append(mu + guardado * sigma)
            guardado = None
            continue
        while True:
            u1 = generador_u.next_u()
            u2 = generador_u.next_u()
            v1 = 2.0 * u1 - 1.0
            v2 = 2.0 * u2 - 1.0
            w = v1 * v1 + v2 * v2
            if w >= 1.0 or w <= 1e-10:
                continue
            break
        factor = math.sqrt(-2.0 * math.log(w) / w)
        z0 = v1 * factor
        z1 = v2 * factor
        muestras.append(mu + z0 * sigma)
        guardado = z1
    return muestras[:n]

def gen_geometrica(generador_u, p):
    u = generador_u.next_u()
    while u <= 1e-10:
        u = generador_u.next_u()
    return math.ceil(math.log(u) / math.log(1.0 - p))

def gen_pascal(generador_u, k, p, n):
    muestras = []
    for _ in range(n):
        suma = 0
        for _ in range(k):
            suma += gen_geometrica(generador_u, p)
        muestras.append(suma)
    return muestras

def gen_binomial(generador_u, n_ensayos, p, n):
    muestras = []
    for _ in range(n):
        exitos = 0
        for _ in range(n_ensayos):
            if generador_u.next_u() < p:
                exitos += 1
        muestras.append(exitos)
    return muestras

def gen_hipergeometrica(generador_u, N, K, n_muestra, n):
    muestras = []
    for _ in range(n):
        exitos = 0
        exitos_restantes = K
        total_restantes = N
        for _ in range(n_muestra):
            if generador_u.next_u() < (exitos_restantes / total_restantes):
                exitos += 1
                exitos_restantes -= 1
            total_restantes -= 1
        muestras.append(exitos)
    return muestras

def gen_poisson(generador_u, lam, n):
    L = math.exp(-lam)
    muestras = []
    for _ in range(n):
        k = 0
        p = 1.0
        while True:
            u = generador_u.next_u()
            while u <= 1e-10:
                u = generador_u.next_u()
            p *= u
            if p <= L:
                break
            k += 1
        muestras.append(k)
    return muestras

def gen_empirica_discreta(generador_u, valores, probabilidades, n):
    acum = []
    suma = 0.0
    for p in probabilidades:
        suma += p
        acum.append(suma)
    if abs(suma - 1.0) > 1e-6:
        acum = [c / suma for c in acum]
    muestras = []
    for _ in range(n):
        u = generador_u.next_u()
        for i, cdf in enumerate(acum):
            if u <= cdf:
                muestras.append(valores[i])
                break
    return muestras

# ---------- Tests estadisticos ----------

def calcular_estadisticas_basicas(muestras, mu_teorico, var_teorico):
    mu_muestral = np.mean(muestras)
    var_muestral = np.var(muestras, ddof=1)
    if mu_teorico != 0:
        err_mu = abs(mu_muestral - mu_teorico) / mu_teorico
    else:
        err_mu = abs(mu_muestral)
    if var_teorico != 0:
        err_var = abs(var_muestral - var_teorico) / var_teorico
    else:
        err_var = abs(var_muestral)
    return {
        "media_teorica": float(mu_teorico),
        "media_muestral": float(round(mu_muestral, 6)),
        "error_media_%": float(round(err_mu * 100, 2)),
        "var_teorica": float(var_teorico),
        "var_muestral": float(round(var_muestral, 6)),
        "error_var_%": float(round(err_var * 100, 2))
    }

def test_kolmogorov_smirnov(muestras, dist_name, *args):
    if dist_name == 'gamma':
        k, lam = args
        d, p = stats.ks_1samp(muestras, stats.gamma.cdf, args=(k, 0, 1/lam))
    elif dist_name == 'uniform':
        a, b = args
        d, p = stats.ks_1samp(muestras, stats.uniform.cdf, args=(a, b - a))
    elif dist_name == 'expon':
        lam = args[0]
        d, p = stats.ks_1samp(muestras, stats.expon.cdf, args=(0, 1/lam))
    elif dist_name == 'norm':
        mu, sigma = args
        d, p = stats.ks_1samp(muestras, stats.norm.cdf, args=(mu, sigma))
    else:
        return None
    return {
        "estadistico_D": round(float(d), 6),
        "p_value": round(float(p), 6),
        "pasa_test_05": bool(p > 0.05)
    }

def test_chi_cuadrado(muestras, pmf_teorica, *args):
    conteo = Counter(muestras)
    categorias = sorted(conteo.keys())
    n_total = len(muestras)
    f_obs = []
    f_esp = []
    for c in categorias:
        prob = pmf_teorica(c, *args)
        esperado = prob * n_total
        if esperado >= 0.5:
            f_obs.append(conteo[c])
            f_esp.append(esperado)
    if len(f_obs) < 2:
        return {"chi2": None, "p_value": None, "pasa_test_05": None}
    suma_obs = sum(f_obs)
    suma_esp = sum(f_esp)
    if abs(suma_obs - suma_esp) > 1e-9:
        f_esp = [e * suma_obs / suma_esp for e in f_esp]
    chi2, p = stats.chisquare(f_obs, f_exp=f_esp)
    return {
        "chi2": round(float(chi2), 4),
        "p_value": round(float(p), 4),
        "pasa_test_05": bool(p > 0.05)
    }

# ---------- Graficos ----------

def graficar(muestras, nombre, params, tipo="continua"):
    os.makedirs("resultados", exist_ok=True)
    plt.figure(figsize=(10, 6))
    if tipo == "continua":
        plt.hist(muestras, bins=50, density=True, alpha=0.6, color='g', label='Muestral')
        x = np.linspace(min(muestras), max(muestras), 200)
        if nombre == "Uniforme":
            a, b = params
            y = [1.0/(b-a) if a<=v<=b else 0 for v in x]
            plt.plot(x, y, 'r-', lw=2, label='Teorica')
        elif nombre == "Exponencial":
            lam = params[0]
            plt.plot(x, lam * np.exp(-lam * x), 'r-', lw=2, label='Teorica')
        elif nombre == "Gamma":
            k, lam = params
            plt.plot(x, stats.gamma.pdf(x, k, scale=1.0/lam), 'r-', lw=2, label='Teorica')
        elif nombre == "Normal":
            mu, sigma = params
            plt.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', lw=2, label='Teorica')
    else:
        vals, counts = np.unique(muestras, return_counts=True)
        plt.bar(vals, counts/len(muestras), alpha=0.6, color='b', label='Muestral')
        if nombre == "Poisson":
            plt.plot(vals, stats.poisson.pmf(vals, params[0]), 'ro', ms=4, label='Teorica')
        elif nombre == "Binomial":
            plt.plot(vals, stats.binom.pmf(vals, int(params[0]), params[1]), 'ro', ms=4, label='Teorica')
    plt.title(f"Distribucion {nombre}")
    plt.xlabel("Valor")
    plt.ylabel("Densidad/Probabilidad")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"resultados/{nombre.lower()}.png")
    plt.close()

# ---------- Tablas para consola ----------

def mostrar_tabla_dist(nombre, params_str, stats_res, test_res, n):
    sep = "=" * 62
    print(f"\n{sep}")
    print(f"  {nombre.upper()}")
    print(f"  Parametros: {params_str}  |  n = {n}")
    print(sep)
    print(f"  {'Magnitud':<20} {'Teorico':<12} {'Muestral':<12} {'Error %':<8}")
    print(f"  {'-'*52}")
    print(f"  {'Media':<20} {stats_res['media_teorica']:<12.4f} {stats_res['media_muestral']:<12.4f} {stats_res['error_media_%']:<8.2f}")
    print(f"  {'Varianza':<20} {stats_res['var_teorica']:<12.4f} {stats_res['var_muestral']:<12.4f} {stats_res['error_var_%']:<8.2f}")
    if test_res:
        p = test_res.get('p_value', 'N/A')
        pasa = "SI" if test_res.get('pasa_test_05') else "NO"
        if test_res.get('chi2'):
            print(f"\n  Test Chi-cuadrado: chi2 = {test_res['chi2']},  p-value = {p},  Pasa = {pasa}")
        else:
            print(f"\n  Test Kolmogorov-Smirnov: D = {test_res.get('estadistico_D', 'N/A')},  p-value = {p},  Pasa = {pasa}")
    print(sep)

def mostrar_tabla_resumen(resultados):
    sep = "=" * 80
    print(f"\n{sep}")
    print(f"  RESUMEN GENERAL - TODAS LAS DISTRIBUCIONES")
    print(sep)
    print(f"  {'Distribucion':<16} {'Media':<20} {'Error%':<8} {'Var':<20} {'Error%':<8} {'Test':<6}")
    print(f"  {'-'*78}")
    for r in resultados:
        s = r['stats']
        media = f"{s['media_teorica']:.2f} -> {s['media_muestral']:.2f}"
        var = f"{s['var_teorica']:.2f} -> {s['var_muestral']:.2f}"
        if r['test'] and r['test'].get('pasa_test_05') is not None:
            test = "PASA" if r['test']['pasa_test_05'] else "NO"
        else:
            test = "-"
        print(f"  {r['nombre']:<16} {media:<20} {s['error_media_%']:<8.2f} {var:<20} {s['error_var_%']:<8.2f} {test:<6}")
    print(sep)

def ejecutar_una(u_gen, nombre, args_n, params, probs=None, metodo="inversa"):
    if nombre == "uniforme":
        a, b = params
        m = gen_uniforme(u_gen, a, b, args_n)
        s = calcular_estadisticas_basicas(m, (a+b)/2, (b-a)**2/12)
        t = test_kolmogorov_smirnov(m, 'uniform', a, b)
        return m, s, t, f"Uniforme({a},{b})", f"a={a}, b={b}"
    elif nombre == "exponencial":
        lam = params[0]
        m = gen_exponencial(u_gen, lam, args_n)
        s = calcular_estadisticas_basicas(m, 1/lam, 1/lam**2)
        t = test_kolmogorov_smirnov(m, 'expon', lam)
        return m, s, t, "Exponencial", f"lambda={lam}"
    elif nombre == "gamma":
        k, lam = int(params[0]), params[1]
        m = gen_gamma_entera(u_gen, k, lam, args_n)
        s = calcular_estadisticas_basicas(m, k/lam, k/lam**2)
        t = test_kolmogorov_smirnov(m, 'gamma', k, lam)
        return m, s, t, "Gamma", f"k={k}, lambda={lam}"
    elif nombre == "normal":
        mu, sigma = params
        m = gen_normal_polar(u_gen, mu, sigma, args_n) if metodo == "polar" else gen_normal(u_gen, mu, sigma, args_n)
        s = calcular_estadisticas_basicas(m, mu, sigma**2)
        t = test_kolmogorov_smirnov(m, 'norm', mu, sigma)
        return m, s, t, "Normal", f"mu={mu}, sigma={sigma}"
    elif nombre == "poisson":
        lam = params[0]
        m = gen_poisson(u_gen, lam, args_n)
        s = calcular_estadisticas_basicas(m, lam, lam)
        t = test_chi_cuadrado(m, stats.poisson.pmf, lam)
        return m, s, t, "Poisson", f"lambda={lam}"
    elif nombre == "pascal":
        k, p = int(params[0]), params[1]
        m = gen_pascal(u_gen, k, p, args_n)
        mu_t, var_t = k/p, k*(1-p)/p**2
        s = calcular_estadisticas_basicas(m, mu_t, var_t)
        t = test_chi_cuadrado(m, lambda x, kk, pp: stats.nbinom.pmf(x-kk, kk, pp), k, p)
        return m, s, t, "Pascal", f"k={k}, p={p}"
    elif nombre == "binomial":
        n_ens, p = int(params[0]), params[1]
        m = gen_binomial(u_gen, n_ens, p, args_n)
        mu_t, var_t = n_ens*p, n_ens*p*(1-p)
        s = calcular_estadisticas_basicas(m, mu_t, var_t)
        t = test_chi_cuadrado(m, stats.binom.pmf, n_ens, p)
        return m, s, t, "Binomial", f"n={n_ens}, p={p}"
    elif nombre == "hiper":
        N, K, nm = int(params[0]), int(params[1]), int(params[2])
        m = gen_hipergeometrica(u_gen, N, K, nm, args_n)
        mu_t = nm * (K / N)
        var_t = nm * (K / N) * ((N - K) / N) * ((N - nm) / (N - 1))
        s = calcular_estadisticas_basicas(m, mu_t, var_t)
        t = test_chi_cuadrado(m, stats.hypergeom.pmf, N, K, nm)
        return m, s, t, "Hipergeometrica", f"N={N}, K={K}, n={nm}"
    elif nombre == "empirica":
        if probs is None:
            print("ERROR: faltan --probs")
            return None, None, None, None, None
        valores = [int(v) for v in params]
        ps = probs
        if abs(sum(ps) - 1.0) > 0.001:
            ps = [p / sum(ps) for p in ps]
        m = gen_empirica_discreta(u_gen, valores, ps, args_n)
        mu_t = sum(v * p for v, p in zip(valores, ps))
        var_t = sum(((v - mu_t)**2) * p for v, p in zip(valores, ps))
        s = calcular_estadisticas_basicas(m, mu_t, var_t)
        t = test_chi_cuadrado(m, lambda x, vals, probs: probs[vals.index(x)] if x in vals else 0.0, valores, ps)
        return m, s, t, "Empirica", f"valores={valores}"
    return None, None, None, None, None

# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="TP2.2 - Generadores de Variables Aleatorias")
    parser.add_argument("--dist", type=str, default="",
                        help="uniforme|exponencial|gamma|normal|pascal|binomial|hiper|poisson|empirica")
    parser.add_argument("--n", type=int, default=10000)
    parser.add_argument("--params", nargs="+", type=float)
    parser.add_argument("--probs", nargs="+", type=float, help="Probs para empirica")
    parser.add_argument("--metodo", type=str, default="inversa", help="inversa|polar")
    parser.add_argument("--all", action="store_true", help="Ejecutar todas las distribuciones")
    args = parser.parse_args()

    u_gen = GeneradorUniforme(metodo="GCL")

    if args.all:
        os.makedirs("resultados", exist_ok=True)
        todas = [
            ("uniforme",    [0, 10],           None),
            ("exponencial", [2.0],             None),
            ("gamma",       [5, 2.0],          None),
            ("normal",      [0, 1],            None),
            ("poisson",     [4.5],             None),
            ("pascal",      [3, 0.5],          None),
            ("binomial",    [10, 0.3],         None),
            ("hiper",       [50, 20, 10],      None),
            ("empirica",    [1, 2, 3],         [0.2, 0.5, 0.3]),
        ]
        resumenes = []
        for dist, params, probs in todas:
            res = ejecutar_una(u_gen, dist, args.n, params, probs, args.metodo)
            muestras, stats_res, test_res, nombre, pstr = res
            if muestras is None:
                continue
            graficar(muestras, nombre, params, "continua" if dist != "empirica" else "discreta")
            mostrar_tabla_dist(nombre, pstr, stats_res, test_res, args.n)
            resumenes.append({"nombre": nombre, "stats": stats_res, "test": test_res})
            with open(f"resultados/{dist}_resumen.json", "w") as f:
                json.dump({"distribucion": dist, "n": args.n, "parametros": params,
                           "estadisticas": stats_res, "test_bondad": test_res}, f, indent=4)
        mostrar_tabla_resumen(resumenes)
        return

    if not args.dist:
        parser.print_help()
        return

    res = ejecutar_una(u_gen, args.dist, args.n, args.params, args.probs, args.metodo)
    muestras, stats_res, test_res, nombre, pstr = res
    if muestras is None:
        print(f"ERROR: distribucion '{args.dist}' no reconocida")
        return

    # inferir tipo para grafico
    continuas = ["uniforme", "exponencial", "gamma", "normal"]
    tipo = "continua" if args.dist in continuas else "discreta"
    graficar(muestras, nombre, args.params, tipo)

    mostrar_tabla_dist(nombre, pstr, stats_res, test_res, args.n)

    os.makedirs("resultados", exist_ok=True)
    with open(f"resultados/{args.dist}_resumen.json", "w") as f:
        json.dump({"distribucion": args.dist, "n": args.n, "parametros": args.params,
                   "estadisticas": stats_res, "test_bondad": test_res}, f, indent=4)
    print(f"Resultados guardados en resultados/")

if __name__ == "__main__":
    main()
