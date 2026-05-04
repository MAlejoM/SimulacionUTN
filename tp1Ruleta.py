#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP 1.1 - SIMULACIÓN DE UNA RULETA
Trabajo práctico de Simulación - UTN FRRO
Autor: Estudiante
Fecha: Mayo 2026

Este programa simula el funcionamiento de una ruleta francesa (0-36)
y realiza análisis estadísticos con visualización de resultados.
"""

import argparse
import random
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from collections import Counter


# =====================================================================
# FASE 1: ESTRUCTURA BASE & CLI
# =====================================================================

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


def validate_inputs(args) -> bool:
    """
    Valida los parámetros ingresados.
    
    Args:
        args: Argumentos parseados
    
    Returns:
        bool: True si válido, False si hay error
    """
    if not (0 <= args.elegido <= 36):
        print(f"❌ Error: Número elegido debe estar entre 0 y 36. Recibido: {args.elegido}")
        return False
    
    if args.corridas <= 0:
        print(f"❌ Error: Corridas debe ser positivo. Recibido: {args.corridas}")
        return False
    
    if args.tiradas <= 0:
        print(f"❌ Error: Tiradas debe ser positivo. Recibido: {args.tiradas}")
        return False
    
    return True


# =====================================================================
# FASE 2: SIMULACIÓN DE RULETA
# =====================================================================

def simular_tirada() -> int:
    """
    Simula una tirada de la ruleta (0-36).
    
    Returns:
        int: Número resultado de la tirada (0-36)
    """
    return random.randint(0, 36)


def simular_corrida(tiradas: int, numero_elegido: int) -> Dict:
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
    resultados = [simular_tirada() for _ in range(tiradas)]
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


def simular_multiples_corridas(corridas: int, tiradas: int, numero_elegido: int) -> Dict:
    """
    Ejecuta múltiples corridas de la simulación.
    
    Args:
        corridas: Número de corridas
        tiradas: Tiradas por corrida
        numero_elegido: Número elegido
    
    Returns:
        Dict: Datos agregados de todas las corridas
    """
    print(f"\n🎲 Ejecutando {corridas} corridas de {tiradas} tiradas cada una...")
    print(f"   Número elegido: {numero_elegido}")
    
    todas_corridas = []
    aciertos_por_corrida = []
    frecuencias_relativas = []
    todas_tiradas = []
    
    for i in range(corridas):
        if (i + 1) % max(1, corridas // 10) == 0:
            print(f"   Progreso: {i + 1}/{corridas} corridas completadas")
        
        corrida = simular_corrida(tiradas, numero_elegido)
        todas_corridas.append(corrida)
        aciertos_por_corrida.append(corrida['aciertos'])
        frecuencias_relativas.append(corrida['frecuencia_relativa'])
        todas_tiradas.extend(corrida['resultados'])
    
    print(f"   ✓ Simulación completada: {corridas * tiradas} tiradas totales")
    
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


# =====================================================================
# FASE 3: ESTADÍSTICAS
# =====================================================================

def calcular_estadisticas(datos_simulacion: Dict) -> Dict:
    """
    Calcula estadísticas sobre los resultados de la simulación.
    
    Args:
        datos_simulacion: Diccionario retornado por simular_multiples_corridas()
    
    Returns:
        Dict: Estadísticas calculadas
    """
    aciertos = datos_simulacion['aciertos_por_corrida']
    frecuencias_rel = datos_simulacion['frecuencias_relativas']
    tiradas_por_corrida = datos_simulacion['tiradas_por_corrida']
    numero_elegido = datos_simulacion['numero_elegido']
    
    # Estadísticas de aciertos por corrida
    media_aciertos = np.mean(aciertos)
    varianza_aciertos = np.var(aciertos, ddof=1)  # Varianza muestral
    desvio_aciertos = np.std(aciertos, ddof=1)
    
    # Estadísticas de frecuencia relativa
    media_freq_rel = np.mean(frecuencias_rel)
    varianza_freq_rel = np.var(frecuencias_rel, ddof=1)
    desvio_freq_rel = np.std(frecuencias_rel, ddof=1)
    
    # Probabilidades teóricas
    prob_teorica = 1 / 37
    prob_empirica = media_freq_rel
    
    # Desviación esperada (teórica)
    varianza_teorica = prob_teorica * (1 - prob_teorica) / tiradas_por_corrida
    desvio_teorica = np.sqrt(varianza_teorica)
    
    # Frecuencias de todos los números (0-36)
    counter_tiradas = Counter(datos_simulacion['todas_tiradas'])
    frecuencias_numeros = {i: counter_tiradas.get(i, 0) for i in range(37)}
    
    return {
        'media_aciertos': media_aciertos,
        'varianza_aciertos': varianza_aciertos,
        'desvio_aciertos': desvio_aciertos,
        'media_freq_rel': media_freq_rel,
        'varianza_freq_rel': varianza_freq_rel,
        'desvio_freq_rel': desvio_freq_rel,
        'prob_teorica': prob_teorica,
        'prob_empirica': prob_empirica,
        'varianza_teorica': varianza_teorica,
        'desvio_teorica': desvio_teorica,
        'frecuencias_numeros': frecuencias_numeros,
        'aciertos_por_corrida': aciertos,
        'frecuencias_relativas': frecuencias_rel
    }


# =====================================================================
# FASE 4: VISUALIZACIÓN - 8+ GRÁFICAS
# =====================================================================

def crear_directorio_resultados(directorio: str = 'resultados'):
    """Crea directorio para guardar gráficas si no existe."""
    Path(directorio).mkdir(exist_ok=True)
    return directorio


def graficar_resultados(datos_simulacion: Dict, estadisticas: Dict, dir_resultados: str = 'resultados'):
    """
    Genera 8+ gráficas de análisis.
    
    Args:
        datos_simulacion: Datos de la simulación
        estadisticas: Estadísticas calculadas
        dir_resultados: Directorio donde guardar las gráficas
    """
    print(f"\n📊 Generando gráficas en directorio '{dir_resultados}'...")
    
    numero_elegido = datos_simulacion['numero_elegido']
    aciertos = estadisticas['aciertos_por_corrida']
    freq_rel = estadisticas['frecuencias_relativas']
    corridas = datos_simulacion['corridas']
    tiradas_por_corrida = datos_simulacion['tiradas_por_corrida']
    
    # =====================================================================
    # GRÁFICA 1: Histograma de frecuencias del número elegido
    # =====================================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(aciertos, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
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
    print(f"   ✓ Gráfica 1: Histograma de aciertos")
    
    # =====================================================================
    # GRÁFICA 2: Distribución normal (TCL) - Teórica vs Empírica
    # =====================================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Histograma normalizado
    counts, bins, patches = ax.hist(aciertos, bins=20, density=True, 
                                     color='steelblue', alpha=0.6, 
                                     edgecolor='black', label='Distribución Empírica')
    
    # Curva normal teórica
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
    print(f"   ✓ Gráfica 2: Distribución normal (TCL)")
    
    # =====================================================================
    # GRÁFICA 3: Evolución de aciertos acumulados (convergencia)
    # =====================================================================
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
    print(f"   ✓ Gráfica 3: Evolución aciertos acumulados")
    
    # =====================================================================
    # GRÁFICA 4: Heatmap de frecuencias por número (0-36)
    # =====================================================================
    fig, ax = plt.subplots(figsize=(14, 4))
    
    numeros = list(range(37))
    frecuencias = [estadisticas['frecuencias_numeros'][i] for i in numeros]
    
    colors = ['red' if i == numero_elegido else 'steelblue' for i in numeros]
    bars = ax.bar(numeros, frecuencias, color=colors, edgecolor='black', alpha=0.7)
    
    # Destacar número elegido
    bars[numero_elegido].set_color('red')
    bars[numero_elegido].set_alpha(0.9)
    
    ax.axhline(np.mean(frecuencias), color='green', linestyle='--', 
               linewidth=2, label=f'Media: {np.mean(frecuencias):.0f}')
    
    ax.set_xlabel('Número de la Ruleta')
    ax.set_ylabel('Frecuencia Absoluta')
    ax.set_title(f'Distribución de Frecuencias: Todos los Números (0-36)\nNúmero elegido: {numero_elegido} (rojo)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(range(0, 37, 3), rotation=0)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/04_distribucion_frecuencias_numeros.png', dpi=150)
    plt.close()
    print(f"   ✓ Gráfica 4: Heatmap frecuencias por número")
    
    # =====================================================================
    # GRÁFICA 5: Box plot de aciertos por corrida
    # =====================================================================
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
    print(f"   ✓ Gráfica 5: Box plot de aciertos")
    
    # =====================================================================
    # GRÁFICA 6: Q-Q plot (normalidad - TCL)
    # =====================================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    
    stats.probplot(aciertos, dist="norm", plot=ax)
    ax.set_title('Q-Q Plot: Prueba de Normalidad (TCL)\nComparación: Datos vs Distribución Normal')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/06_qq_plot_normalidad.png', dpi=150)
    plt.close()
    print(f"   ✓ Gráfica 6: Q-Q plot normalidad")
    
    # =====================================================================
    # GRÁFICA 7: Probabilidad teórica vs empírica (comparativo)
    # =====================================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos = np.arange(2)
    probs = [estadisticas['prob_teorica'], estadisticas['prob_empirica']]
    labels = ['Teórica\n(1/37)', f'Empírica\n({corridas} corridas)']
    colors_bars = ['green', 'steelblue']
    
    bars = ax.bar(x_pos, probs, color=colors_bars, edgecolor='black', alpha=0.7, width=0.5)
    
    # Agregar valores en barras
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
    print(f"   ✓ Gráfica 7: Probabilidad teórica vs empírica")
    
    # =====================================================================
    # GRÁFICA 8: Media móvil de frecuencia relativa (convergencia)
    # =====================================================================
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Media móvil con ventana de 5 corridas
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
    print(f"   ✓ Gráfica 8: Media móvil convergencia")
    
    # =====================================================================
    # GRÁFICA ADICIONAL 9: Varianza empírica vs teórica
    # =====================================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos_var = np.arange(2)
    varianzas = [estadisticas['varianza_teorica'], estadisticas['varianza_aciertos']]
    labels_var = ['Teórica', f'Empírica']
    colors_var = ['green', 'steelblue']
    
    bars = ax.bar(x_pos_var, varianzas, color=colors_var, edgecolor='black', alpha=0.7, width=0.5)
    
    for i, (bar, var) in enumerate(zip(bars, varianzas)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{var:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_ylabel('Varianza')
    ax.set_title(f'Comparativo: Varianza Teórica vs Empírica\n(Aciertos por corrida)')
    ax.set_xticks(x_pos_var)
    ax.set_xticklabels(labels_var)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{dir_resultados}/09_varianza_teorica_vs_empirica.png', dpi=150)
    plt.close()
    print(f"   ✓ Gráfica 9: Varianza teórica vs empírica")
    
    print(f"✓ Todas las gráficas generadas exitosamente")


# =====================================================================
# FASE 5: EXPORTACIÓN DE DATOS
# =====================================================================

def exportar_datos(datos_simulacion: Dict, estadisticas: Dict, 
                   dir_resultados: str = 'resultados', nombre_archivo: str = 'datos_simulacion.json'):
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
            'varianza_teorica': float(estadisticas['varianza_teorica']),
            'desvio_teorica': float(estadisticas['desvio_teorica']),
            'diferencia_varianzas': float(estadisticas['varianza_aciertos'] - estadisticas['varianza_teorica'])
        },
        'frecuencias_numeros': {str(k): v for k, v in estadisticas['frecuencias_numeros'].items()},
        'aciertos_por_corrida': [int(a) for a in estadisticas['aciertos_por_corrida']],
        'frecuencias_relativas': [float(f) for f in estadisticas['frecuencias_relativas']]
    }
    
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump(datos_exportacion, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Datos exportados a: {archivo_json}")


def generar_resumen_texto(datos_simulacion: Dict, estadisticas: Dict) -> str:
    """
    Genera un resumen de los resultados en formato texto.
    
    Args:
        datos_simulacion: Datos de simulación
        estadisticas: Estadísticas calculadas
    
    Returns:
        str: Resumen de resultados
    """
    resumen = f"""
╔════════════════════════════════════════════════════════════════════════╗
║              RESUMEN DE RESULTADOS - SIMULACIÓN DE RULETA              ║
╚════════════════════════════════════════════════════════════════════════╝

📊 PARÁMETROS DE SIMULACIÓN:
  • Número de corridas: {datos_simulacion['corridas']}
  • Tiradas por corrida: {datos_simulacion['tiradas_por_corrida']:,}
  • Número elegido: {datos_simulacion['numero_elegido']}
  • Total de tiradas: {datos_simulacion['total_tiradas']:,}
  • Total de aciertos: {datos_simulacion['total_aciertos']:,}

📈 ESTADÍSTICAS - ACIERTOS POR CORRIDA:
  • Media de aciertos: {estadisticas['media_aciertos']:.4f}
  • Varianza empírica: {estadisticas['varianza_aciertos']:.6f}
  • Desviación estándar: {estadisticas['desvio_aciertos']:.6f}
  • Valor esperado teórico: {datos_simulacion['tiradas_por_corrida'] / 37:.4f}

📊 ESTADÍSTICAS - FRECUENCIA RELATIVA:
  • Media de f.r.: {estadisticas['media_freq_rel']:.6f}
  • Varianza de f.r.: {estadisticas['varianza_freq_rel']:.8f}
  • Desviación estándar de f.r.: {estadisticas['desvio_freq_rel']:.8f}

🎲 PROBABILIDADES:
  • Probabilidad teórica: {estadisticas['prob_teorica']:.6f} (1/37)
  • Probabilidad empírica: {estadisticas['prob_empirica']:.6f}
  • Diferencia: {abs(estadisticas['prob_teorica'] - estadisticas['prob_empirica']):.6f}
  • Error relativo: {abs(estadisticas['prob_teorica'] - estadisticas['prob_empirica']) / estadisticas['prob_teorica'] * 100:.2f}%

📐 VARIANZA:
  • Varianza teórica: {estadisticas['varianza_teorica']:.8f}
  • Varianza empírica: {estadisticas['varianza_aciertos']:.8f}
  • Diferencia: {estadisticas['varianza_aciertos'] - estadisticas['varianza_teorica']:.8f}

✅ ANÁLISIS:
  • Número más frecuente: {max(estadisticas['frecuencias_numeros'], key=estadisticas['frecuencias_numeros'].get)} 
    (frecuencia: {max(estadisticas['frecuencias_numeros'].values())})
  • Número menos frecuente: {min(estadisticas['frecuencias_numeros'], key=estadisticas['frecuencias_numeros'].get)} 
    (frecuencia: {min(estadisticas['frecuencias_numeros'].values())})
  • Aciertos máximos en una corrida: {max(estadisticas['aciertos_por_corrida'])}
  • Aciertos mínimos en una corrida: {min(estadisticas['aciertos_por_corrida'])}

╔════════════════════════════════════════════════════════════════════════╗
║                           FIN DEL RESUMEN                             ║
╚════════════════════════════════════════════════════════════════════════╝
"""
    return resumen


# =====================================================================
# FASE 6: MAIN & INTEGRACIÓN
# =====================================================================

def main():
    """Función principal: orquesta todo el flujo."""
    print("=" * 70)
    print("SIMULACIÓN DE RULETA FRANCESA CON ANÁLISIS ESTADÍSTICO")
    print("=" * 70)
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Validar entrada
    if not validate_inputs(args):
        sys.exit(1)
    
    # Configurar semilla si se proporciona
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
        print(f"\n🔐 Semilla aleatoria fijada a: {args.seed}")
    
    # Crear directorio de resultados
    dir_resultados = crear_directorio_resultados()
    
    # Ejecutar simulación
    print("\n" + "=" * 70)
    datos_simulacion = simular_multiples_corridas(
        args.corridas,
        args.tiradas,
        args.elegido
    )
    
    # Calcular estadísticas
    print("\n📊 Calculando estadísticas...")
    estadisticas = calcular_estadisticas(datos_simulacion)
    print("   ✓ Estadísticas calculadas")
    
    # Generar gráficas
    print("\n" + "=" * 70)
    graficar_resultados(datos_simulacion, estadisticas, dir_resultados)
    
    # Exportar datos
    print("\n" + "=" * 70)
    exportar_datos(datos_simulacion, estadisticas, dir_resultados)
    
    # Mostrar resumen
    print("\n" + "=" * 70)
    resumen = generar_resumen_texto(datos_simulacion, estadisticas)
    print(resumen)
    
    # Guardar resumen en archivo de texto
    archivo_resumen = os.path.join(dir_resultados, 'resumen_resultados.txt')
    with open(archivo_resumen, 'w', encoding='utf-8') as f:
        f.write(resumen)
    print(f"💾 Resumen también guardado en: {archivo_resumen}")
    
    print("\n" + "=" * 70)
    print("✓ SIMULACIÓN COMPLETADA EXITOSAMENTE")
    print(f"📁 Resultados guardados en: {os.path.abspath(dir_resultados)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
