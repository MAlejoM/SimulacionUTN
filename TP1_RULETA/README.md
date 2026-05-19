# TP1_1
# Ejecución básica (100 corridas, 1000 tiradas, número 17)
python tp1Ruleta.py

# Con parámetros personalizados
python tp1Ruleta.py -c 100 -n 1000 -e 17

# Con semilla para reproducibilidad
python tp1Ruleta.py -c 50 -n 500 -e 0 -s 42

# Ver ayuda
python tp1Ruleta.py --help

# TP1_2
# Simular estrategia Martingala con capital infinito (10 corridas, 1000 tiradas)
python tp1_2_ruleta.py -c 10 -n 1000 -s m -a i

# Simular estrategia D'Alembert con capital finito (50 corridas, 500 tiradas)
python tp1_2_ruleta.py -c 50 -n 500 -s d -a f

# Simular estrategia D'Alembert con capital finito definiendo el pozo inicial en 5000 fichas
python tp1_2_ruleta.py -c 50 -n 500 -s d -a f --pozo 5000

# Simular la estrategia "Otra" (Paroli) con capital finito
python tp1_2_ruleta.py -c 30 -n 800 -s o -a f

# Ver ayuda y descripción de los parámetros
python tp1_2_ruleta.py --help