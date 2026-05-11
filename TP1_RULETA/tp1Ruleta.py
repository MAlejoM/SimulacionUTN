#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP 1.1 - SIMULACIÓN DE UNA RULETA

Este programa simula el funcionamiento de una ruleta francesa (0-36)
y realiza análisis estadísticos con visualización de resultados.
"""

import argparse
import random
import json
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from collections import Counter


#estructura base
def parse_arguments():
    """
    Parsea argumentos de línea de comandos.
    
    Argumentos:
        -c, --corridas: Número de corridas (default: 100)
        -n, --tiradas: Tiradas por corrida (default: 1000)
        -e, --elegido: Número elegido (0-36, default: 17)
        -s, --seed: Semilla aleatoria para reproducibilidad (opcional)
    
    Returns:
        argparse.Namespace: Objeto con argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Simulador de Ruleta Francesa con Análisis Estadístico",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python tp1Ruleta.py -c 100 -n 1000 -e 17
  python tp1Ruleta.py -c 50 -n 500 -e 0 -s 42
        """
    )
    
    parser.add_argument('-c', '--corridas', type=int, default=100,
                        help='Número de corridas (default: 100)')
    parser.add_argument('-n', '--tiradas', type=int, default=1000,
                        help='Tiradas por corrida (default: 1000)')
    parser.add_argument('-e', '--elegido', type=int, default=17,
                        help='Número elegido 0-36 (default: 17)')
    parser.add_argument('-s', '--seed', type=int, default=None,
                        help='Semilla aleatoria para reproducibilidad (opcional)')
    
    args = parser.parse_args()
    return args


def validate_inputs(args):
    """
    Valida los parámetros ingresados.
    
    Args:
        args: Argumentos parseados
    
    Returns:
        bool: True si válido, False si hay error
    """
    if not (0 <= args.elegido <= 36):
        print(f"[Error] El número elegido debe estar entre 0 y 36. Valor recibido: {args.elegido}")
        return False
    
    if args.corridas <= 0:
        print(f"[Error] La cantidad de corridas debe ser mayor a 0. Valor recibido: {args.corridas}")
        return False
    
    if args.tiradas <= 0:
        print(f"[Error] La cantidad de tiradas debe ser mayor a 0. Valor recibido: {args.tiradas}")
        return False
    
    return True


def simular_tirada(): #se genera de valor aleatorio 
    """
    Simula una tirada de la ruleta (0-36).
    
    Returns:
        int: Número resultado de la tirada (0-36)
    """
    return random.randint(0, 36)


def simular_corrida(tiradas, numero_elegido):
    """
    Simula una corrida completa de N tiradas.
    
    Args:
        tiradas: Número de tiradas a realizar
        numero_elegido: Número en el que se apuesta
    
    Returns:
        Dict: Diccionario con estadísticas de la corrida:
            - 'resultados': lista de resultados
            - 'aciertos': cantidad de aciertos
            - 'frecuencia_relativa': fr = aciertos / tiradas
            - 'frecuencia_esperada': 1/37
            - 'frecuencias_por_numero': Counter de todos los números
    """
    resultados = [simular_tirada() for _ in range(tiradas)] #se guarda en lista
    aciertos = sum(1 for r in resultados if r == numero_elegido)
    frecuencia_relativa = aciertos / tiradas
    frecuencia_esperada = 1 / 37
    frecuencias_por_numero = dict(Counter(resultados))
    
    return {
        'resultados': resultados,
        'aciertos': aciertos,
        'frecuencia_relativa': frecuencia_relativa,
        'frecuencia_esperada': frecuencia_esperada,
        'frecuencias_por_numero': frecuencias_por_numero
    }


def simular_multiples_corridas(corridas, tiradas, numero_elegido):

    todas_corridas = []
    aciertos_por_corrida = []
    frecuencias_relativas = []
    todas_tiradas = []

    for _ in range(corridas):

        corrida = simular_corrida(tiradas, numero_elegido)

        todas_corridas.append(corrida)
        aciertos_por_corrida.append(corrida['aciertos'])
        frecuencias_relativas.append(corrida['frecuencia_relativa'])

        todas_tiradas.extend(corrida['resultados'])

    return {
        'corridas': corridas,
        'tiradas_por_corrida': tiradas,
        'numero_elegido': numero_elegido,
        'todas_corridas': todas_corridas,
        'aciertos_por_corrida': aciertos_por_corrida,
        'frecuencias_relativas': frecuencias_relativas,
        'todas_tiradas': todas_tiradas,
        'total_tiradas': corridas * tiradas,
        'total_aciertos': sum(aciertos_por_corrida)
    }

#calc d estadisticas
def calcular_estadisticas(datos):

    aciertos = datos['aciertos_por_corrida']
    frecuencias_rel = datos['frecuencias_relativas']

    n = datos['tiradas_por_corrida']

    media_aciertos = np.mean(aciertos)
    varianza_aciertos = np.var(aciertos, ddof=1)
    desvio_aciertos = np.std(aciertos, ddof=1)

    media_freq_rel = np.mean(frecuencias_rel)
    varianza_freq_rel = np.var(frecuencias_rel, ddof=1)
    desvio_freq_rel = np.std(frecuencias_rel, ddof=1)

    prob_teorica = 1 / 37

    # Varianza teórica de cantidad de aciertos
    varianza_teorica_aciertos = n * prob_teorica * (1 - prob_teorica)

    # Varianza teórica de frecuencia relativa
    varianza_teorica_freq = (
        prob_teorica * (1 - prob_teorica)
    ) / n

    counter = Counter(datos['todas_tiradas'])

    frecuencias_numeros = {
        i: counter.get(i, 0)
        for i in range(37)
    }

    return {
        'media_aciertos': media_aciertos,
        'varianza_aciertos': varianza_aciertos,
        'desvio_aciertos': desvio_aciertos,

        'media_freq_rel': media_freq_rel,
        'varianza_freq_rel': varianza_freq_rel,
        'desvio_freq_rel': desvio_freq_rel,

        'prob_teorica': prob_teorica,
        'prob_empirica': media_freq_rel,

        'varianza_teorica_aciertos': varianza_teorica_aciertos,
        'varianza_teorica_freq': varianza_teorica_freq,

        'frecuencias_numeros': frecuencias_numeros,

        'aciertos_por_corrida': aciertos,
        'frecuencias_relativas': frecuencias_rel
    }


def crear_directorio_resultados(directorio='resultados'):
    """Crea directorio para guardar gráficas si no existe."""
    base_dir = Path(__file__).resolve().parent
    ruta = Path(directorio)
    if not ruta.is_absolute():
        ruta = base_dir / ruta
    ruta.mkdir(parents=True, exist_ok=True)
    return str(ruta)


def graficar_resultados(datos_simulacion, estadisticas, dir_resultados='resultados'):
    """
    Genera 8+ gráficas de análisis.
    
    Args:
        datos_simulacion: Datos de la simulación
        estadisticas: Estadísticas calculadas
        dir_resultados: Directorio donde guardar las gráficas
    """
    print(f"\nGenerando gráficos en '{dir_resultados}'...")
    
    numero_elegido = datos_simulacion['numero_elegido']
    aciertos = estadisticas['aciertos_por_corrida']
    freq_rel = estadisticas['frecuencias_relativas']
    corridas = datos_simulacion['corridas']
    tiradas_por_corrida = datos_simulacion['tiradas_por_corrida']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(aciertos, bins='auto', color='steelblue', edgecolor='black', alpha=0.7)
    ax.axvline(estadisticas['media_aciertos'], color='red', linestyle='--', 
               linewidth=2, label=f'Media: {estadisticas["media_aciertos"]:.2f}')
    ax.axvline(tiradas_por_corrida / 37, color='green', linestyle='--', 
               linewidth=2, label=f'Teórica: {tiradas_por_corrida / 37:.2f}')
    ax.set_xlabel('Cantidad de Aciertos')
    ax.set_ylabel('Frecuencia')
    ax.set_title(f'Histograma: Aciertos del Número {numero_elegido}\n({corridas} corridas de {tiradas_por_corrida} tiradas)')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/01_histograma_aciertos.png', dpi=150)
    plt.close()
    print("  [1/9] Histograma de aciertos")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    counts, bins, patches = ax.hist(aciertos, bins='auto', density=True, 
                                     color='steelblue', alpha=0.6, 
                                     edgecolor='black', label='Distribución Empírica')
    
    mu = estadisticas['media_aciertos']
    sigma = estadisticas['desvio_aciertos']
    x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
    ax.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=2, 
            label='Distribución Normal Teórica')
    
    ax.set_xlabel('Cantidad de Aciertos')
    ax.set_ylabel('Densidad de Probabilidad')
    ax.set_title(f'Teorema Central del Límite: Distribución Normal\nμ={mu:.2f}, σ={sigma:.2f}')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/02_distribucion_normal_tcl.png', dpi=150)
    plt.close()
    print("  [2/9] Distribución normal (TCL)")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    aciertos_acumulados = np.cumsum(aciertos)
    tiradas_acumuladas = np.arange(1, len(aciertos) + 1) * tiradas_por_corrida
    freq_acumulada = aciertos_acumulados / tiradas_acumuladas
    
    ax.plot(range(1, corridas + 1), freq_acumulada, 'b-', linewidth=1.5, label='Frecuencia Relativa Acumulada')
    ax.axhline(1/37, color='red', linestyle='--', linewidth=2, label='Probabilidad Teórica (1/37)')
    ax.fill_between(range(1, corridas + 1), 1/37 - 0.005, 1/37 + 0.005, 
                     alpha=0.2, color='green', label='Banda ±0.005')
    
    ax.set_xlabel('Número de Corrida')
    ax.set_ylabel('Frecuencia Relativa Acumulada')
    ax.set_title('Convergencia: Frecuencia Relativa Acumulada vs Probabilidad Teórica')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_ylim([0, 0.1])
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/03_convergencia_acumulada.png', dpi=150)
    plt.close()
    print("  [3/9] Evolución acumulada")
    
    fig, ax = plt.subplots(figsize=(14, 5))
    numeros = list(range(37))
    frecuencias = [estadisticas['frecuencias_numeros'][i] for i in numeros]
    colores = ['red' if i == numero_elegido else 'steelblue' for i in numeros]

    ax.bar(numeros, frecuencias, color=colores, edgecolor='black')
    ax.axhline(np.mean(frecuencias), color='green', linestyle='--', label='Frecuencia promedio')
    ax.set_xlabel('Número')
    ax.set_ylabel('Frecuencia')
    ax.set_title('Frecuencia de aparición de cada número')
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/04_frecuencia_numeros.png', dpi=150)
    plt.close()
    print("  [4/9] Frecuencia por número")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(aciertos, vert=True, patch_artist=True, widths=0.5)
    
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    
    ax.axhline(tiradas_por_corrida / 37, color='red', linestyle='--', 
               linewidth=2, label=f'Valor Esperado: {tiradas_por_corrida / 37:.2f}')
    
    ax.set_ylabel('Cantidad de Aciertos')
    ax.set_title(f'Box Plot: Distribución de Aciertos por Corrida\n({corridas} corridas)')
    ax.set_xticklabels(['Aciertos'])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/05_boxplot_aciertos.png', dpi=150)
    plt.close()
    print("  [5/9] Box plot de aciertos")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    stats.probplot(aciertos, dist="norm", plot=ax)
    ax.set_title('Q-Q Plot: Prueba de Normalidad (TCL)\nComparación: Datos vs Distribución Normal')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/06_qq_plot_normalidad.png', dpi=150)
    plt.close()
    print("  [6/9] Q-Q plot")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos = np.arange(2)
    probs = [estadisticas['prob_teorica'], estadisticas['prob_empirica']]
    labels = ['Teórica\n(1/37)', f'Empírica\n({corridas} corridas)']
    colors_bars = ['green', 'steelblue']
    
    bars = ax.bar(x_pos, probs, color=colors_bars, edgecolor='black', alpha=0.7, width=0.5)
    
    for i, (bar, prob) in enumerate(zip(bars, probs)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{prob:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_ylabel('Probabilidad de Acierto')
    ax.set_title(f'Comparativo: Probabilidad Teórica vs Empírica\nNúmero elegido: {numero_elegido}')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.set_ylim([0, max(probs) * 1.2])
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/07_prob_teorica_vs_empirica.png', dpi=150)
    plt.close()
    print("  [7/9] Probabilidad teórica vs empírica")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ventana = min(5, corridas // 10) if corridas > 10 else 1
    media_movil = np.convolve(freq_rel, np.ones(ventana)/ventana, mode='valid')
    corridas_movil = range(ventana, len(freq_rel) + 1)
    
    ax.plot(range(1, corridas + 1), freq_rel, 'b-', alpha=0.4, linewidth=1, label='Frecuencia Relativa')
    ax.plot(corridas_movil, media_movil, 'r-', linewidth=2, label=f'Media Móvil (ventana={ventana})')
    ax.axhline(1/37, color='green', linestyle='--', linewidth=2, label='Probabilidad Teórica (1/37)')
    
    ax.set_xlabel('Número de Corrida')
    ax.set_ylabel('Frecuencia Relativa')
    ax.set_title('Convergencia: Media Móvil de Frecuencia Relativa')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_ylim([0, 0.1])
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/08_media_movil_convergencia.png', dpi=150)
    plt.close()
    print("  [8/9] Media móvil")
    
    fig, ax = plt.subplots(figsize=(8, 5))
    valores = [estadisticas['varianza_teorica_aciertos'], estadisticas['varianza_aciertos']]
    labels = ['Teórica', 'Empírica']

    ax.bar(labels, valores, color=['green', 'steelblue'], edgecolor='black')
    ax.set_ylabel('Varianza')
    ax.set_title('Varianza teórica y empírica de aciertos')

    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/09_varianza.png', dpi=150)
    plt.close()
    print("  [9/9] Varianza teórica vs empírica")


def exportar_datos(datos_simulacion, estadisticas,
                   dir_resultados='resultados', nombre_archivo='datos_simulacion.json'):
    """
    Exporta datos de la simulación a archivo JSON.
    
    Args:
        datos_simulacion: Datos de simulación
        estadisticas: Estadísticas calculadas
        dir_resultados: Directorio para guardar
        nombre_archivo: Nombre del archivo JSON
    """
    archivo_json = os.path.join(dir_resultados, nombre_archivo)
    
    datos_exportacion = {
        'parametros': {
            'corridas': datos_simulacion['corridas'],
            'tiradas_por_corrida': datos_simulacion['tiradas_por_corrida'],
            'numero_elegido': datos_simulacion['numero_elegido'],
            'total_tiradas': datos_simulacion['total_tiradas'],
            'total_aciertos': datos_simulacion['total_aciertos']
        },
        'estadisticas': {
        'media_aciertos': float(estadisticas['media_aciertos']),
        'varianza_aciertos': float(estadisticas['varianza_aciertos']),
        'desvio_aciertos': float(estadisticas['desvio_aciertos']),

        'media_freq_rel': float(estadisticas['media_freq_rel']),
        'varianza_freq_rel': float(estadisticas['varianza_freq_rel']),
        'desvio_freq_rel': float(estadisticas['desvio_freq_rel']),

        'prob_teorica': float(estadisticas['prob_teorica']),
        'prob_empirica': float(estadisticas['prob_empirica']),

        'varianza_teorica_aciertos': float(
            estadisticas['varianza_teorica_aciertos']
        ),

        'varianza_teorica_freq': float(
            estadisticas['varianza_teorica_freq']
        )
    },
        'frecuencias_numeros': {str(k): v for k, v in estadisticas['frecuencias_numeros'].items()},
        'aciertos_por_corrida': [int(a) for a in estadisticas['aciertos_por_corrida']],
        'frecuencias_relativas': [float(f) for f in estadisticas['frecuencias_relativas']]
    }
    
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump(datos_exportacion, f, indent=2, ensure_ascii=False)
    
    print(f"Datos exportados en: {archivo_json}")


def generar_resumen_texto(datos_simulacion, estadisticas):
    """
    Genera un resumen de los resultados en formato texto.
    
    Args:
        datos_simulacion: Datos de simulación
        estadisticas: Estadísticas calculadas
    
    Returns:
        str: Resumen de resultados
    """
    resumen = f"""
RESUMEN DE RESULTADOS - SIMULACIÓN DE RULETA

Parámetros:
- Corridas: {datos_simulacion['corridas']}
- Tiradas por corrida: {datos_simulacion['tiradas_por_corrida']:,}
- Número elegido: {datos_simulacion['numero_elegido']}
- Total de tiradas: {datos_simulacion['total_tiradas']:,}
- Total de aciertos: {datos_simulacion['total_aciertos']:,}

Aciertos por corrida:
- Media: {estadisticas['media_aciertos']:.4f}
- Varianza empírica: {estadisticas['varianza_aciertos']:.6f}
- Desviación estándar: {estadisticas['desvio_aciertos']:.6f}
- Valor esperado teórico: {datos_simulacion['tiradas_por_corrida'] / 37:.4f}

Frecuencia relativa:
- Media: {estadisticas['media_freq_rel']:.6f}
- Varianza: {estadisticas['varianza_freq_rel']:.8f}
- Desviación estándar: {estadisticas['desvio_freq_rel']:.8f}

Probabilidades:
- Teórica: {estadisticas['prob_teorica']:.6f} (1/37)
- Empírica: {estadisticas['prob_empirica']:.6f}
- Diferencia absoluta: {abs(estadisticas['prob_teorica'] - estadisticas['prob_empirica']):.6f}
- Error relativo: {abs(estadisticas['prob_teorica'] - estadisticas['prob_empirica']) / estadisticas['prob_teorica'] * 100:.2f}%

Varianza:
- Teórica: {estadisticas['varianza_teorica_aciertos']:.8f}
- Empírica: {estadisticas['varianza_aciertos']:.8f}
- Diferencia absoluta: {abs(estadisticas['varianza_aciertos'] - estadisticas['varianza_teorica_aciertos']):.8f}

Análisis:
- Número más frecuente: {max(estadisticas['frecuencias_numeros'], key=estadisticas['frecuencias_numeros'].get)} (frecuencia: {max(estadisticas['frecuencias_numeros'].values())})
- Número menos frecuente: {min(estadisticas['frecuencias_numeros'], key=estadisticas['frecuencias_numeros'].get)} (frecuencia: {min(estadisticas['frecuencias_numeros'].values())})
- Aciertos máximos en una corrida: {max(estadisticas['aciertos_por_corrida'])}
- Aciertos mínimos en una corrida: {min(estadisticas['aciertos_por_corrida'])}
"""
    return resumen


def main():

    args = parse_arguments()

    if not validate_inputs(args):
        sys.exit(1)

    print("Iniciando simulación...\n")

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
        print(f"Semilla fijada en: {args.seed}")

    dir_resultados = crear_directorio_resultados()

    datos = simular_multiples_corridas(
        args.corridas,
        args.tiradas,
        args.elegido
    )

    estadisticas = calcular_estadisticas(datos)

    graficar_resultados(
        datos,
        estadisticas,
        dir_resultados
    )

    exportar_datos(
        datos,
        estadisticas,
        dir_resultados
    )

    resumen = generar_resumen_texto(
        datos,
        estadisticas
    )

    print("\n" + resumen)

    archivo_resumen = os.path.join(
        dir_resultados,
        'resumen_resultados.txt'
    )

    with open(archivo_resumen, 'w', encoding='utf-8') as f:
        f.write(resumen)

    print(f"Resumen guardado en: {archivo_resumen}")
    print(f"Resultados disponibles en: {os.path.abspath(dir_resultados)}")


if __name__ == "__main__":
    main()
