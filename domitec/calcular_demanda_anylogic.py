import os
import sys
import pandas as pd
import numpy as np

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "CH21_20260815_csv.csv")

# 1. Cargar y limpiar datos
print("Cargando dataset...")
df_raw = pd.read_csv(DATA_PATH, sep=';', encoding='latin1', dtype=str)
df_raw.columns = [
    'Anio', 'VentasXnegocio', 'Mes', 'Cliente', 'RubroDes',
    'PresentacionDes', 'Pedidos', 'Pendientes', 'Despachadas',
    'Cancelado', 'Pct_Perdida_Vta'
]

# Filtrar totales
df = df_raw[df_raw['Anio'].astype(str).str.strip().str.lower() != 'total'].copy()

# Parsear Pedidos numéricos
def parse_spanish_int(val):
    if pd.isna(val):
        return 0
    val_str = str(val).strip().replace('.', '').replace(',', '.')
    try:
        return int(round(float(val_str)))
    except:
        return 0

df['Pedidos'] = df['Pedidos'].apply(parse_spanish_int)

# Limpiar campos de texto
for col in ['Cliente', 'RubroDes', 'Mes', 'Anio']:
    df[col] = df[col].astype(str).str.strip()

# Mapeo de meses y creación de columna de Periodo (20 meses)
meses_map = {
    'Ene.': '01', 'Feb.': '02', 'Mar.': '03', 'Abr.': '04', 'May.': '05', 'Jun.': '06',
    'Jul.': '07', 'Ago.': '08', 'Sept.': '09', 'Oct.': '10', 'Nov.': '11', 'Dic.': '12'
}
df['Mes_num'] = df['Mes'].map(meses_map)
df['Periodo'] = df['Anio'] + '-' + df['Mes_num']

# 1. Agrupación de Clientes (3 Perfiles)
# - Maxiconsumo: Únicamente los registros del cliente "MAXICONSUMO S.A."
# - Grandes Clientes: Únicamente los registros de "SUPERM. MAYORISTAS MAKRO" / "SUPERMERCADOS MAYORISTAS MAKRO", "TREOLAND SA" y "INC S. A." / "INC S. A. (Carrefour)"
# - Red Propia: Todos los demás clientes que no sean los 4 mencionados arriba.
grandes_clientes_set = {
    "SUPERMERCADOS MAYORISTAS MAKRO",
    "SUPERM. MAYORISTAS MAKRO",
    "TREOLAND SA",
    "INC S. A.",
    "INC S. A. (CARREFOUR)",
    "INC S.A."
}

def clasificar_cliente(c):
    c_clean = str(c).strip().upper()
    if c_clean == "MAXICONSUMO S.A.":
        return "Maxiconsumo"
    elif c_clean in grandes_clientes_set:
        return "Grandes Clientes"
    else:
        return "Red Propia"

df['Perfil_Cliente'] = df['Cliente'].apply(clasificar_cliente)

# 2. Agrupación de Productos (10 Familias)
# Mapeo de normalización de RubroDes para asegurar los nombres exactos pedidos
# Familias pedidas:
# Lavandina Común, Líquido Desinfectante, Lavavajilla, Lavandina Concentrada, Líquido Lavar Ropa,
# Suavizante, Promopack, Detergente Concentrado, Líquido Limpiador, Líquido Bactericida
familias_map = {
    'LAVANDINA COMUN': 'Lavandina Común',
    'LIQUIDO DESINFECTANTE': 'Líquido Desinfectante',
    'LAVAVAJILLA': 'Lavavajilla',
    'LAVANDINA CONCENTRADA': 'Lavandina Concentrada',
    'LIQUIDO LAVAR ROPA': 'Líquido Lavar Ropa',
    'SUAVIZANTE': 'Suavizante',
    'PROMOPACK': 'Promopack',
    'DETERGENTE CONCENTRADO': 'Detergente Concentrado',
    'LIQUIDO LIMPIADOR': 'Líquido Limpiador',
    'LIQUIDO BACTERICIDA': 'Líquido Bactericida'
}

# Normalizar con fallback
df['Producto'] = df['RubroDes'].map(lambda x: familias_map.get(x.upper(), x.title()))

# Lista fija ordenada de perfiles, productos y los 20 periodos
perfiles_orden = ["Maxiconsumo", "Grandes Clientes", "Red Propia"]
productos_orden = [
    "Lavandina Común",
    "Líquido Desinfectante",
    "Lavavajilla",
    "Lavandina Concentrada",
    "Líquido Lavar Ropa",
    "Suavizante",
    "Promopack",
    "Detergente Concentrado",
    "Líquido Limpiador",
    "Líquido Bactericida"
]

periodos_unicos = sorted(df['Periodo'].unique())
print(f"Total de meses identificados ({len(periodos_unicos)}): {periodos_unicos}")

# 3. Agregación Mensual (Suma de Pedidos por Perfil_Cliente, Producto y Periodo)
df_agrupado = df.groupby(['Perfil_Cliente', 'Producto', 'Periodo'])['Pedidos'].sum().reset_index()

# Crear el grid completo (Producto Cartesiano de 3 Perfiles x 10 Productos x 20 Periodos)
# para asegurar que meses sin pedidos cuenten estrictamente como 0
grid = pd.MultiIndex.from_product(
    [perfiles_orden, productos_orden, periodos_unicos],
    names=['Perfil_Cliente', 'Producto', 'Periodo']
).to_frame().reset_index(drop=True)

df_completo = pd.merge(grid, df_agrupado, on=['Perfil_Cliente', 'Producto', 'Periodo'], how='left')
df_completo['Pedidos'] = df_completo['Pedidos'].fillna(0)

# 4. Cálculo Estadístico: Media (μ) y Desviación Estándar poblacional (σ, ddof=0)
resultados = []

for perfil in perfiles_orden:
    for prod in productos_orden:
        sub = df_completo[(df_completo['Perfil_Cliente'] == perfil) & (df_completo['Producto'] == prod)]
        valores_mensuales = sub['Pedidos'].values
        
        # Estadísticas
        media = np.mean(valores_mensuales)
        desv_pob = np.std(valores_mensuales, ddof=0) # Poblacional
        desv_muestral = np.std(valores_mensuales, ddof=1) # Muestral para referencia
        
        resultados.append({
            'Perfil_Cliente': perfil,
            'Producto': prod,
            'Media_Mensual': media,
            'Desv_Estandar': desv_pob,
            'Desv_Muestral': desv_muestral,
            'Total_20_Meses': np.sum(valores_mensuales)
        })

df_res = pd.DataFrame(resultados)

# 5. Salida en formato Markdown
print("\n" + "="*80)
print("TABLA DE PARÁMETROS ESTADÍSTICOS DE DEMANDA MENSUAL PARA ANYLOGIC")
print("="*80)

# Imprimir tabla Markdown
print("| Perfil_Cliente | Producto | Media_Mensual | Desv_Estandar |")
print("| :--- | :--- | :---: | :---: |")
for _, row in df_res.iterrows():
    print(f"| {row['Perfil_Cliente']} | {row['Producto']} | {row['Media_Mensual']:.2f} | {row['Desv_Estandar']:.2f} |")

# Guardar CSV de salida
output_csv = os.path.join(BASE_DIR, "output", "demanda_mensual_anylogic_perfil_producto.csv")
df_res[['Perfil_Cliente', 'Producto', 'Media_Mensual', 'Desv_Estandar']].to_csv(output_csv, index=False, sep=';', decimal=',')
print(f"\nArchivo CSV guardado en: {output_csv}")
