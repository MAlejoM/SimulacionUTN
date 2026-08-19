import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "CH21_20260815_csv.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

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

text_cols = ['VentasXnegocio', 'Cliente', 'RubroDes', 'Mes']
for col in text_cols:
    df[col] = df[col].astype(str).str.strip()

meses_map = {'Ene.': 1, 'Feb.': 2, 'Mar.': 3, 'Abr.': 4, 'May.': 5, 'Jun.': 6, 'Jul.': 7, 'Ago.': 8, 'Sept.': 9, 'Oct.': 10, 'Nov.': 11, 'Dic.': 12}
df['Mes_num'] = df['Mes'].map(meses_map)
df['Anio_num'] = df['Anio'].astype(int)
df['Periodo'] = df['Anio_num'].astype(str) + '-' + df['Mes_num'].astype(str).str.zfill(2)

# 1. Agrupación General de Productos (por Rubro / Familia)
rubros = df.groupby('RubroDes').agg(
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

# Variabilidad mensual por Rubro
rubro_mensual = df.groupby(['RubroDes', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
stats_rubro = pd.DataFrame({
    'Media_Mensual': rubro_mensual.mean(axis=1),
    'Std_Mensual': rubro_mensual.std(axis=1),
    'Min_Mensual': rubro_mensual.min(axis=1),
    'Max_Mensual': rubro_mensual.max(axis=1)
}).reset_index()
stats_rubro['CV'] = stats_rubro['Std_Mensual'] / stats_rubro['Media_Mensual']

rubros_final = pd.merge(rubros, stats_rubro, on='RubroDes')

# Clasificación ABC de Rubros
def abc_rubro(acum):
    if acum <= 80:
        return 'A (Principal)'
    elif acum <= 95:
        return 'B (Medio)'
    else:
        return 'C (Marginal)'
rubros_final['Clasificacion_ABC'] = rubros_final['Share_Acum_%'].apply(abc_rubro)

# Guardar resumen simplificado
rubros_final.to_csv(os.path.join(OUTPUT_DIR, "resumen_productos_familias.csv"), index=False, sep=';', decimal=',')

print("=== RESUMEN FAMILIAS DE PRODUCTOS ===")
print(rubros_final[['RubroDes', 'Pedidos', 'Share_%', 'Share_Acum_%', 'Media_Mensual', 'CV', 'Fill_Rate_%', 'Clasificacion_ABC']])

# 2. Resumen Clientes por Canal
canales = df.groupby('VentasXnegocio').agg(
    Pedidos=('Pedidos', 'sum'),
    Despachadas=('Despachadas', 'sum'),
    Cancelado=('Cancelado', 'sum'),
    Clientes=('Cliente', 'nunique')
).reset_index()
canales['Share_%'] = (canales['Pedidos'] / canales['Pedidos'].sum()) * 100
canales['Fill_Rate_%'] = (canales['Despachadas'] / canales['Pedidos']) * 100
canales_mensual = df.groupby(['VentasXnegocio', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
cv_canal = (canales_mensual.std(axis=1) / canales_mensual.mean(axis=1)).reset_index(name='CV_Demanda')
canales = pd.merge(canales, cv_canal, on='VentasXnegocio').sort_values(by='Pedidos', ascending=False)
canales.to_csv(os.path.join(OUTPUT_DIR, "resumen_canales_simplificado.csv"), index=False, sep=';', decimal=',')

print("\n=== RESUMEN CANALES DE CLIENTES ===")
print(canales)
