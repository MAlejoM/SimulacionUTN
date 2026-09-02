import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "CH21_20260815_csv.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Cargar datos
df_raw = pd.read_csv(DATA_PATH, sep=';', encoding='latin1', dtype=str)
df_raw.columns = ['Anio', 'VentasXnegocio', 'Mes', 'Cliente', 'RubroDes', 'PresentacionDes', 'Pedidos', 'Pendientes', 'Despachadas', 'Cancelado', 'Pct_Perdida_Vta']
df = df_raw[df_raw['Anio'].astype(str).str.strip().str.lower() != 'total'].copy()

def parse_spanish_int(val):
    if pd.isna(val):
        return 0
    val_str = str(val).strip().replace('.', '').replace(',', '.')
    try:
        return int(round(float(val_str)))
    except:
        return 0

for col in ['Pedidos', 'Pendientes', 'Despachadas', 'Cancelado']:
    df[col] = df[col].apply(parse_spanish_int)

text_cols = ['VentasXnegocio', 'Cliente', 'RubroDes', 'Mes', 'Anio']
for col in text_cols:
    df[col] = df[col].astype(str).str.strip()

meses_map = {'Ene.': 1, 'Feb.': 2, 'Mar.': 3, 'Abr.': 4, 'May.': 5, 'Jun.': 6, 'Jul.': 7, 'Ago.': 8, 'Sept.': 9, 'Oct.': 10, 'Nov.': 11, 'Dic.': 12}
df['Mes_num'] = df['Mes'].map(meses_map)
df['Anio_num'] = df['Anio'].astype(int)
df['Periodo'] = df['Anio_num'].astype(str) + '-' + df['Mes_num'].astype(str).str.zfill(2)

# Mapeo y filtro de productos (6 familias consolidadas, exclusión de Promopack y Bactericida)
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

df_filtered = df[df['RubroDes'].isin(rubro_map.keys())].copy()
df_filtered['Producto'] = df_filtered['RubroDes'].map(rubro_map)

canal_map = {
    'MAXICONSUMO': 'Maxiconsumo',
    'GRANDES CLIENTES': 'Grandes Clientes',
    'RED PROPIA': 'Red Propia'
}
df_filtered['Canal'] = df_filtered['VentasXnegocio'].map(canal_map)

# 1. Agrupación General de Productos (6 Familias)
rubros = df_filtered.groupby('Producto').agg(
    Pedidos=('Pedidos', 'sum'),
    Despachadas=('Despachadas', 'sum'),
    Cancelado=('Cancelado', 'sum'),
    Pendientes=('Pendientes', 'sum'),
    Clientes=('Cliente', 'nunique')
).reset_index()

rubros = rubros.sort_values(by='Pedidos', ascending=False).reset_index(drop=True)
rubros['Share_%'] = (rubros['Pedidos'] / rubros['Pedidos'].sum()) * 100
rubros['Share_Acum_%'] = rubros['Share_%'].cumsum()
rubros['Fill_Rate_%'] = (rubros['Despachadas'] / rubros['Pedidos']) * 100
rubros['Cancelado_%'] = (rubros['Cancelado'] / rubros['Pedidos']) * 100

# Variabilidad mensual por Producto (sobre los 20 meses)
rubro_mensual = df_filtered.groupby(['Producto', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
stats_rubro = pd.DataFrame({
    'Media_Mensual': rubro_mensual.mean(axis=1),
    'Std_Mensual': rubro_mensual.std(axis=1),
    'Min_Mensual': rubro_mensual.min(axis=1),
    'Max_Mensual': rubro_mensual.max(axis=1)
}).reset_index()
stats_rubro['CV'] = stats_rubro['Std_Mensual'] / stats_rubro['Media_Mensual']

rubros_final = pd.merge(rubros, stats_rubro, on='Producto')

# Clasificación ABC de Productos
def abc_rubro(acum):
    if acum <= 80:
        return 'A (Principal)'
    elif acum <= 95:
        return 'B (Medio)'
    else:
        return 'C (Marginal)'
rubros_final['Clasificacion_ABC'] = rubros_final['Share_Acum_%'].apply(abc_rubro)

# Guardar resumen simplificado de productos
rubros_final.to_csv(os.path.join(OUTPUT_DIR, "resumen_productos_familias.csv"), index=False, sep=';', decimal=',')

print("=== RESUMEN FAMILIAS DE PRODUCTOS (6 CONSOLIDADAS) ===")
print(rubros_final[['Producto', 'Pedidos', 'Share_%', 'Share_Acum_%', 'Media_Mensual', 'CV', 'Fill_Rate_%', 'Clasificacion_ABC']])

# 2. Resumen Clientes por Canal
canales = df_filtered.groupby('Canal').agg(
    Pedidos=('Pedidos', 'sum'),
    Despachadas=('Despachadas', 'sum'),
    Cancelado=('Cancelado', 'sum'),
    Pendientes=('Pendientes', 'sum'),
    Clientes=('Cliente', 'nunique')
).reset_index()
canales['Share_%'] = (canales['Pedidos'] / canales['Pedidos'].sum()) * 100
canales['Fill_Rate_%'] = (canales['Despachadas'] / canales['Pedidos']) * 100
canales['Cancelado_%'] = (canales['Cancelado'] / canales['Pedidos']) * 100

canales_mensual = df_filtered.groupby(['Canal', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
cv_canal = (canales_mensual.std(axis=1) / canales_mensual.mean(axis=1)).reset_index(name='CV_Demanda')
canales = pd.merge(canales, cv_canal, on='Canal').sort_values(by='Pedidos', ascending=False)
canales.to_csv(os.path.join(OUTPUT_DIR, "resumen_canales_simplificado.csv"), index=False, sep=';', decimal=',')

print("\n=== RESUMEN CANALES DE CLIENTES ===")
print(canales)
