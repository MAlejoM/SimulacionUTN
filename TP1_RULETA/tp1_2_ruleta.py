#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP 1.2 - ESTUDIO ECONÓMICO-MATEMÁTICO DE APUESTAS EN LA RULETA
"""

import argparse
import random
import os
import numpy as np
import matplotlib.pyplot as plt

def parse_arguments():
    parser = argparse.ArgumentParser(description="Simulador de Estrategias de Apuestas en Ruleta")
    parser.add_argument('-c', '--corridas', type=int, required=True, help='Número de corridas')
    parser.add_argument('-n', '--tiradas', type=int, required=True, help='Tiradas por corrida')
    parser.add_argument('-e', '--elegido', type=int, default=0, help='Número elegido (Opcional en este TP)')
    parser.add_argument('-s', '--estrategia', choices=['m', 'd', 'f', 'o'], required=True, 
                        help='Estrategia: m (Martingala), d (D\'Alembert), f (Fibonacci), o (Paroli/Otra)')
    parser.add_argument('-a', '--capital', choices=['i', 'f'], required=True, 
                        help='Capital: i (Infinito), f (Finito)')
    # Parámetro extra interno para definir el pozo inicial si es finito
    parser.add_argument('--pozo', type=float, default=1000.0, help='Capital inicial (solo si es finito)')
    
    return parser.parse_args()

def simular_tirada():
    """ Simula una tirada de la ruleta (0-36). Retorna True si gana la apuesta (Rojo/Negro). """
    resultado = random.randint(0, 36)
    # Apostamos a "Color" (ej. Rojo, que son 18 números). Probabilidad de ganar: 18/37
    # Asumimos que los números del 1 al 18 son la apuesta ganadora para simplificar.
    if 1 <= resultado <= 18:
        return True
    return False

def generar_fibonacci(n):
    """ Genera secuencia de Fibonacci hasta n elementos """
    fib = [1, 1]
    for _ in range(n):
        fib.append(fib[-1] + fib[-2])
    return fib

def simular_estrategia(tiradas, estrategia, tipo_capital, capital_inicial):
    """
    Ejecuta una corrida aplicando una estrategia específica.
    """
    # Configuraciones iniciales
    if tipo_capital == 'i':
        capital = 0  # Si es infinito, medimos el flujo de caja desde 0 (puede ser negativo)
    else:
        capital = capital_inicial
        
    apuesta_base = 1
    apuesta_actual = apuesta_base
    
    # Variables de control
    fibo = generar_fibonacci(tiradas)
    idx_fibo = 0
    victorias_consecutivas_paroli = 0
    bancarrota = False
    
    # Registros históricos
    flujo_caja = []
    apuestas_favorables = [] # 1 si se ganó la apuesta, 0 si se perdió
    
    for _ in range(tiradas):
        # Chequeo de capital finito
        if tipo_capital == 'f':
            if capital <= 0:
                # Bancarrota
                bancarrota = True
                flujo_caja.append(0)
                apuestas_favorables.append(0)
                continue
            
            # Si la apuesta supera mi capital, apuesto lo que me queda
            if apuesta_actual > capital:
                apuesta_actual = capital
        
        # Tirar la ruleta
        gano = simular_tirada()
        
        if gano:
            capital += apuesta_actual
            apuestas_favorables.append(1)
            
            # Ajuste de apuesta según estrategia (WIN)
            if estrategia == 'm':   # Martingala
                apuesta_actual = apuesta_base
            elif estrategia == 'd': # D'Alembert
                apuesta_actual = max(apuesta_base, apuesta_actual - 1)
            elif estrategia == 'f': # Fibonacci
                idx_fibo = max(0, idx_fibo - 2)
                apuesta_actual = fibo[idx_fibo]
            elif estrategia == 'o': # Otra (Paroli / Anti-Martingala)
                victorias_consecutivas_paroli += 1
                if victorias_consecutivas_paroli == 3: # Si gana 3 seguidas, asegura ganancia y reinicia
                    apuesta_actual = apuesta_base
                    victorias_consecutivas_paroli = 0
                else:
                    apuesta_actual *= 2 # Dobla cuando gana
                
        else:
            capital -= apuesta_actual
            apuestas_favorables.append(0)
            
            # Ajuste de apuesta según estrategia (LOSS)
            if estrategia == 'm':   # Martingala
                apuesta_actual *= 2
            elif estrategia == 'd': # D'Alembert
                apuesta_actual += 1
            elif estrategia == 'f': # Fibonacci
                idx_fibo += 1
                apuesta_actual = fibo[idx_fibo]
            elif estrategia == 'o': # Otra (Paroli / Anti-Martingala)
                apuesta_actual = apuesta_base
                victorias_consecutivas_paroli = 0
                
        flujo_caja.append(capital)
        
    return flujo_caja, apuestas_favorables, bancarrota

def main():
    args = parse_arguments()
    
    nombres_estrategia = {'m': 'Martingala', 'd': "D'Alembert", 'f': 'Fibonacci', 'o': 'Paroli (Otra)'}
    estrategia_nombre = nombres_estrategia[args.estrategia]
    tipo_cap_nombre = "Infinito" if args.capital == 'i' else f"Finito (Inicial: {args.pozo})"
    
    print(f"--- SIMULACIÓN TP 1.2 ---")
    print(f"Estrategia: {estrategia_nombre} | Capital: {tipo_cap_nombre}")
    print(f"Corridas: {args.corridas} | Tiradas por corrida: {args.tiradas}\n")
    
    todas_cajas = []
    todas_favorables = []
    quiebras = 0
    
    # 1. Ejecutar las corridas
    for i in range(args.corridas):
        caja, favorables, quebro = simular_estrategia(args.tiradas, args.estrategia, args.capital, args.pozo)
        todas_cajas.append(caja)
        todas_favorables.append(favorables)
        if quebro:
            quiebras += 1
            
    if args.capital == 'f':
        print(f"Bancarrotas registradas: {quiebras} de {args.corridas} corridas ({(quiebras/args.corridas)*100:.2f}%)")

    # 2. Generar Carpeta de Resultados
    if not os.path.exists('resultados_apuestas'):
        os.makedirs('resultados_apuestas')

    n_array = np.arange(1, args.tiradas + 1)
    
    # === GRÁFICA 1: Flujo de caja de UNA corrida (para ver el detalle como pide el boceto) ===
    plt.figure(figsize=(10, 5))
    corrida_ejemplo = todas_cajas[0]
    plt.plot(n_array, corrida_ejemplo, color='red', linewidth=1.5, label='Flujo de caja')
    if args.capital == 'f':
        plt.axhline(y=args.pozo, color='black', linestyle='--', label='Flujo de caja inicial')
    else:
        plt.axhline(y=0, color='black', linestyle='--', label='Flujo de caja inicial (0)')
    plt.title(f'Flujo de Caja - 1 Corrida ({estrategia_nombre})')
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('Capital (cc)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('resultados_apuestas/01_flujo_caja_individual.png')
    plt.close()

    # === GRÁFICA 2: Frecuencia relativa de apuesta favorable ===
    # Calculamos la frecuencia relativa acumulada de la primera corrida
    victorias_acumuladas = np.cumsum(todas_favorables[0])
    frecuencia_relativa = victorias_acumuladas / n_array
    
    plt.figure(figsize=(10, 5))
    plt.plot(n_array, frecuencia_relativa, color='blue', linewidth=1.5)
    plt.axhline(y=18/37, color='green', linestyle='--', label='Prob. Esperada (18/37 ~ 0.486)')
    plt.title(f'Frecuencia Relativa de Apuesta Favorable ({estrategia_nombre})')
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('fr (Frecuencia Relativa)')
    plt.ylim([0, 1])
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('resultados_apuestas/02_frecuencia_apuesta.png')
    plt.close()

    # === GRÁFICA 3: Flujo de caja de MÚLTIPLES corridas simultáneas ===
    plt.figure(figsize=(12, 6))
    for i, caja in enumerate(todas_cajas):
        # Dibujamos todas las corridas con algo de transparencia para que se vean todas
        plt.plot(n_array, caja, alpha=0.6, linewidth=1)
        
    if args.capital == 'f':
        plt.axhline(y=args.pozo, color='black', linestyle='--', linewidth=2, label='Capital Inicial')
    else:
        plt.axhline(y=0, color='black', linestyle='--', linewidth=2, label='Capital 0')
        
    plt.title(f'Flujo de Caja Simultáneo - {args.corridas} Corridas ({estrategia_nombre})')
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('Capital')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('resultados_apuestas/03_flujo_caja_simultaneo.png')
    plt.close()

    print("Gráficas generadas exitosamente en la carpeta 'resultados_apuestas'.")

if __name__ == '__main__':
    main()