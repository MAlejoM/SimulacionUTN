#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP 1.2 - ESTUDIO ECONÓMICO-MATEMÁTICO DE APUESTAS EN LA RULETA
Ejecución en lote de 4 estrategias (Martingala, D'Alembert, Fibonacci, Paroli)
en escenarios de capital Infinito y Finito.
"""

import argparse
import random
import os
import numpy as np
import matplotlib.pyplot as plt

# Configuración de tipos de apuesta: (Casos favorables, Pago por victoria)
TIPOS_APUESTA = {
    'numero': (1, 35),
    'color': (18, 1),
    'docena': (12, 2),
    'par_impar': (18, 1)
}

NOMBRES_ESTRATEGIA = {
    'm': 'Martingala', 
    'd': "D'Alembert", 
    'f': 'Fibonacci', 
    'o': 'Paroli'
}

def parse_arguments():
    parser = argparse.ArgumentParser(description="Simulador de Ruleta 1.2 - Batch Run")
    parser.add_argument('-c', '--corridas', type=int, default=50, help='Número de corridas')
    parser.add_argument('-n', '--tiradas', type=int, default=1000, help='Tiradas por corrida')
    parser.add_argument('-e', '--eleccion', type=int, help='Número elegido para la apuesta (ej. 0 al 36)')
    parser.add_argument('-s', '--estrategia', choices=['m', 'd', 'f', 'o'], help='Estrategia: m (martingala), d (D\'Alembert), f (Fibonacci), o (otra/paroli)')
    parser.add_argument('-a', '--capital', choices=['i', 'f'], help='Tipo de capital: i (infinito), f (finito)')
    parser.add_argument('-t', '--tipo_apuesta', choices=TIPOS_APUESTA.keys(), default='color', help='Tipo de apuesta')
    parser.add_argument('--pozo', type=float, default=10000.0, help='Capital inicial (para escenario finito)')
    parser.add_argument('--apuesta_base', type=float, default=10.0, help='Apuesta inicial')
    return parser.parse_args()

def generar_fibonacci(n):
    fib = [1, 1]
    for _ in range(n):
        fib.append(fib[-1] + fib[-2])
    return fib

def simular_corrida(tiradas, estrategia, tipo_capital, pozo, apuesta_base, tipo_apuesta):
    casos_fav, pago = TIPOS_APUESTA[tipo_apuesta]
    prob_ganar = casos_fav / 37.0
    
    capital = 0 if tipo_capital == 'i' else pozo
    apuesta_actual = apuesta_base
    
    fibo = generar_fibonacci(tiradas)
    idx_fibo = 0
    victorias_paroli = 0
    bancarrota = False
    
    flujo_caja = []
    historial_apuestas = []
    
    for _ in range(tiradas):
        if tipo_capital == 'f' and capital <= 0:
            bancarrota = True
            flujo_caja.append(0)
            historial_apuestas.append(0)
            continue
            
        if tipo_capital == 'f' and apuesta_actual > capital:
            apuesta_actual = capital # All-in con lo que queda
            
        historial_apuestas.append(apuesta_actual)
        
        # Simular ruleta
        tiro = random.random()
        gano = tiro < prob_ganar
        
        if gano:
            capital += apuesta_actual * pago
            
            # Reglas de victoria
            if estrategia == 'm': apuesta_actual = apuesta_base
            elif estrategia == 'd': apuesta_actual = max(apuesta_base, apuesta_actual - apuesta_base)
            elif estrategia == 'f': 
                idx_fibo = max(0, idx_fibo - 2)
                apuesta_actual = fibo[idx_fibo] * apuesta_base
            elif estrategia == 'o': 
                victorias_paroli += 1
                if victorias_paroli == 3:
                    apuesta_actual = apuesta_base
                    victorias_paroli = 0
                else: apuesta_actual *= 2
        else:
            capital -= apuesta_actual
            
            # Reglas de derrota
            if estrategia == 'm': apuesta_actual *= 2
            elif estrategia == 'd': apuesta_actual += apuesta_base
            elif estrategia == 'f': 
                idx_fibo += 1
                apuesta_actual = fibo[idx_fibo] * apuesta_base
            elif estrategia == 'o': 
                apuesta_actual = apuesta_base
                victorias_paroli = 0
                
        flujo_caja.append(capital)
        
    return flujo_caja, historial_apuestas, bancarrota

def main():
    args = parse_arguments()
    
    out_dir = 'resultados_apuestas'
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"=== INICIANDO SIMULACIÓN BATCH ===")
    print(f"Corridas: {args.corridas} | Tiradas: {args.tiradas}")
    print(f"Apuesta Base: {args.apuesta_base} | Pozo (finito): {args.pozo} | Tipo: {args.tipo_apuesta.capitalize()}\n")
    
    resumen_estadistico = []

    estrategias = [args.estrategia] if args.estrategia else ['m', 'd', 'f', 'o']
    capitales = [args.capital] if args.capital else ['i', 'f']
    
    n_array = np.arange(1, args.tiradas + 1)

    for est in estrategias:
        for cap in capitales:
            est_nom = NOMBRES_ESTRATEGIA[est]
            cap_nom = "Infinito" if cap == 'i' else "Finito"
            prefijo = f"{est_nom}_{cap_nom}"
            ref_y = args.pozo if cap == 'f' else 0
            
            todas_cajas = []
            todas_apuestas = []
            bancarrotas = 0
            
            # Ejecutar N corridas
            for _ in range(args.corridas):
                caja, apuestas, quebro = simular_corrida(args.tiradas, est, cap, args.pozo, args.apuesta_base, args.tipo_apuesta)
                todas_cajas.append(caja)
                todas_apuestas.append(apuestas)
                if quebro:
                    bancarrotas += 1

            # --- GRÁFICA 1: ANÁLISIS MICRO (1 Corrida Detallada) ---
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
            
            ax1.plot(n_array, todas_cajas[0], color='crimson')
            ax1.axhline(y=ref_y, color='black', linestyle='--', label='Capital Inicial')
            ax1.set_title(f'Flujo de Caja (1 corrida) - {est_nom} ({cap_nom})')
            ax1.set_ylabel('Capital')
            ax1.grid(alpha=0.3)
            ax1.legend()
            
            ax2.plot(n_array, todas_apuestas[0], color='indigo')
            ax2.set_title(f'Evolución del tamaño de la apuesta')
            ax2.set_xlabel('Número de tiradas')
            ax2.set_ylabel('Monto Apostado')
            ax2.grid(alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f'{out_dir}/01_{prefijo}_Micro.png')
            plt.close()

            # --- GRÁFICA 2: ANÁLISIS MACRO (Flujo Múltiple) ---
            plt.figure(figsize=(10, 5))
            for caja in todas_cajas:
                plt.plot(n_array, caja, alpha=0.5, linewidth=1)
            plt.axhline(y=ref_y, color='black', linestyle='--', linewidth=2, label='Capital Inicial')
            plt.title(f'Flujo de Caja ({args.corridas} corridas) - {est_nom} ({cap_nom})')
            plt.xlabel('Número de tiradas')
            plt.ylabel('Capital')
            plt.legend()
            plt.grid(alpha=0.3)
            plt.savefig(f'{out_dir}/02_{prefijo}_Macro.png')
            plt.close()

            # --- GRÁFICA 3: RENDIMIENTO ESTADÍSTICO (Promedio + Desviación) ---
            plt.figure(figsize=(10, 5))
            cajas_np = np.array(todas_cajas)
            media = np.mean(cajas_np, axis=0)
            std = np.std(cajas_np, axis=0)
            
            plt.plot(n_array, media, color='orange', label='Capital Promedio')
            plt.fill_between(n_array, media - std, media + std, color='orange', alpha=0.2, label='±1 Desv. Estándar')
            plt.axhline(y=ref_y, color='blue', linestyle='--', label='Capital Inicial')
            
            texto_stats = f"Rendimiento Promedio - {est_nom} ({cap_nom})"
            if cap == 'f':
                texto_stats += f"\nBancarrotas: {bancarrotas}/{args.corridas} ({(bancarrotas/args.corridas)*100:.1f}%)"
                
            plt.title(texto_stats)
            plt.xlabel('Número de tiradas')
            plt.ylabel('Capital')
            plt.legend()
            plt.grid(alpha=0.3)
            plt.savefig(f'{out_dir}/03_{prefijo}_Estadistico.png')
            plt.close()

            # Guardar datos para el resumen final
            capital_final_promedio = media[-1]
            tasa_bancarrota = (bancarrotas/args.corridas)*100 if cap == 'f' else 0.0
            max_apuesta = np.max(todas_apuestas)
            
            resumen_estadistico.append({
                'estrategia': est_nom,
                'capital': cap_nom,
                'cap_final_prom': capital_final_promedio,
                'bancarrotas_pct': tasa_bancarrota,
                'apuesta_maxima': max_apuesta
            })

    # Imprimir resumen para pasar a LaTeX
    print("=== RESUMEN DE RESULTADOS (COPIAR ESTO PARA EL INFORME) ===")
    print(f"{'Estrategia':<15} | {'Escenario':<10} | {'Cap. Final Prom.':<18} | {'% Bancarrotas':<15} | {'Apuesta Máx. Histórica':<20}")
    print("-" * 85)
    for r in resumen_estadistico:
        print(f"{r['estrategia']:<15} | {r['capital']:<10} | {r['cap_final_prom']:<18.2f} | {r['bancarrotas_pct']:<13.1f}% | {r['apuesta_maxima']:<20.2f}")
    print("=" * 85)
    print(f"24 Gráficas generadas exitosamente en la carpeta '{out_dir}'.")

if __name__ == '__main__':
    main()