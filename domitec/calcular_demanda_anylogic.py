import os
import sys
import pandas as pd
import numpy as np

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "CH21_20260815_csv.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Cargar y limpiar datos
print("Cargando dataset...")
df_raw = pd.read_csv(DATA_PATH, sep=';', encoding='latin1', dtype=str)
df_raw.columns = [
    'Anio', 'VentasXnegocio', 'Mes', 'Cliente', 'RubroDes',
    'PresentacionDes', 'Pedidos', 'Pendientes', 'Despachadas',
    'Cancelado', 'Pct_Perdida_Vta'
]

# Filtrar fila de totales
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
for col in ['Cliente', 'RubroDes', 'Mes', 'Anio', 'VentasXnegocio', 'PresentacionDes']:
    df[col] = df[col].astype(str).str.strip()

# Mapeo de meses y creación de columna de Periodo (20 meses)
meses_map = {
    'Ene.': '01', 'Feb.': '02', 'Mar.': '03', 'Abr.': '04', 'May.': '05', 'Jun.': '06',
    'Jul.': '07', 'Ago.': '08', 'Sept.': '09', 'Oct.': '10', 'Nov.': '11', 'Dic.': '12'
}
df['Mes_num'] = df['Mes'].map(meses_map)
df['Periodo'] = df['Anio'] + '-' + df['Mes_num']

# 2. Agrupación y Mapeo de Productos (6 Familias Consolidadas)
# - Lavandina Común y Lavandina Concentrada -> "Lavandina"
# - Líquido Desinfectante y Líquido Limpiador -> "Líquido Desinfectante / Limpiador"
# - Lavavajilla, Líquido Lavar Ropa, Suavizante, Detergente Concentrado se mantienen
# - Promopack y Líquido Bactericida quedan excluidos
rubro_map = {
    'LAVANDINA COMUN': 'Lavandina',
    'LAVANDINA CONCENTRADA': 'Lavandina',
    'LIQUIDO DESINFECTANTE': 'Líquido Desinfectante / Limpiador',
    'LIQUIDO LIMPIADOR': 'Líquido Desinfectante / Limpiador',
    'LAVAVAJILLA': 'Lavavajilla',
    'LIQUIDO LAVAR ROPA': 'Líquido Lavar Ropa',
    'SUAVIZANTE': 'Suavizante',
    'DETERGENTE CONCENTRADO': 'Detergente Concentrado'
}

# Filtrar registros que pertenecen a las 6 familias seleccionadas
df_filtered = df[df['RubroDes'].isin(rubro_map.keys())].copy()
df_filtered['Producto'] = df_filtered['RubroDes'].map(rubro_map)

# 3. Clasificación de Clientes en 3 Canales / Perfiles
canal_map = {
    'MAXICONSUMO': 'Maxiconsumo',
    'GRANDES CLIENTES': 'Grandes Clientes',
    'RED PROPIA': 'Red Propia'
}
df_filtered['Perfil_Cliente'] = df_filtered['VentasXnegocio'].map(canal_map)

# Listas ordenadas fijas
perfiles_orden = ["Maxiconsumo", "Grandes Clientes", "Red Propia"]
productos_orden = [
    "Lavandina",
    "Líquido Desinfectante / Limpiador",
    "Lavavajilla",
    "Líquido Lavar Ropa",
    "Suavizante",
    "Detergente Concentrado"
]

periodos_unicos = sorted(df_filtered['Periodo'].unique())
print(f"Total de meses identificados ({len(periodos_unicos)}): {periodos_unicos}")
print(f"Total pedidos incluidos: {df_filtered['Pedidos'].sum():,}")

# 4. Agregación Mensual (Suma de Pedidos por Perfil_Cliente, Producto y Periodo)
df_agrupado = df_filtered.groupby(['Perfil_Cliente', 'Producto', 'Periodo'])['Pedidos'].sum().reset_index()

# Crear grid cartesiano completo (3 Perfiles x 6 Productos x 20 Periodos = 360 combinaciones)
grid = pd.MultiIndex.from_product(
    [perfiles_orden, productos_orden, periodos_unicos],
    names=['Perfil_Cliente', 'Producto', 'Periodo']
).to_frame().reset_index(drop=True)

df_completo = pd.merge(grid, df_agrupado, on=['Perfil_Cliente', 'Producto', 'Periodo'], how='left')
df_completo['Pedidos'] = df_completo['Pedidos'].fillna(0)

# 5. Cálculo Estadístico: Media (μ) y Desviación Estándar poblacional (σ, ddof=0) y muestral (ddof=1)
resultados = []

for perfil in perfiles_orden:
    for prod in productos_orden:
        sub = df_completo[(df_completo['Perfil_Cliente'] == perfil) & (df_completo['Producto'] == prod)]
        valores_mensuales = sub['Pedidos'].values
        
        media = float(np.mean(valores_mensuales))
        desv_pob = float(np.std(valores_mensuales, ddof=0))
        desv_muestral = float(np.std(valores_mensuales, ddof=1))
        cv = (desv_pob / media) if media > 0 else 0.0
        total_vol = float(np.sum(valores_mensuales))
        
        resultados.append({
            'Perfil_Cliente': perfil,
            'Producto': prod,
            'Media_Mensual': media,
            'Desv_Estandar_Pob': desv_pob,
            'Desv_Estandar_Muestral': desv_muestral,
            'CV': cv,
            'Total_20_Meses': total_vol
        })

df_res = pd.DataFrame(resultados)

# 6. Salida por Consola en formato Markdown
print("\n" + "="*85)
print("TABLA DE PARÁMETROS ESTADÍSTICOS DE DEMANDA MENSUAL PARA ANYLOGIC (6 PRODUCTOS)")
print("="*85)

print("| Perfil_Cliente | Producto | Media_Mensual | Desv_Estandar_Pob | Desv_Estandar_Muestral | CV | Total_Pedidos |")
print("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |")
for _, row in df_res.iterrows():
    print(f"| {row['Perfil_Cliente']} | {row['Producto']} | {row['Media_Mensual']:.2f} | {row['Desv_Estandar_Pob']:.2f} | {row['Desv_Estandar_Muestral']:.2f} | {row['CV']:.4f} | {row['Total_20_Meses']:,.0f} |")

# Guardar CSV de salida
output_csv = os.path.join(OUTPUT_DIR, "demanda_mensual_anylogic_perfil_producto.csv")
df_res[['Perfil_Cliente', 'Producto', 'Media_Mensual', 'Desv_Estandar_Pob', 'Desv_Estandar_Muestral', 'CV', 'Total_20_Meses']].to_csv(
    output_csv, index=False, sep=';', decimal=','
)
print(f"\nArchivo CSV guardado exitosamente en: {output_csv}")
