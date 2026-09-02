"""
================================================================================
ANÁLISIS INTEGRAL DE DEMANDA - DOMITEC S.A.
PROYECTO DE SIMULACIÓN EN ANYLOGIC (EFECTO LÁTIGO & CADENA DE SUMINISTRO)
================================================================================
Este script realiza el análisis integral de demanda a partir de los datos reales
de Domitec (2025 - 2026), considerando la taxonomía actualizada:
- 6 Familias Consolidadas:
  1. Lavandina (Común + Concentrada)
  2. Líquido Desinfectante / Limpiador (Desinfectante + Limpiador)
  3. Lavavajilla
  4. Líquido Lavar Ropa
  5. Suavizante
  6. Detergente Concentrado
- Exclusión de: Promopack y Líquido Bactericida.
- 3 Canales de Clientes: Maxiconsumo, Grandes Clientes, Red Propia.

Genera:
1. Clasificación y segmentación de clientes (ABC, RFM, Variabilidad, Concentración HHI, Nivel de Servicio).
2. Agrupación y clasificación de productos (6 familias, SKUs, Matriz ABC-XYZ).
3. Parámetros para AnyLogic (Ajuste de distribuciones estocásticas, variabilidad por canal / efecto látigo, capacidad).
4. Reportes CSV detallados y gráficos visuales de alta calidad.
================================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

# Configuración de estilo visual
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.autolayout'] = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "CH21_20260815_csv.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 1. CARGA Y LIMPIEZA DE DATOS
# ------------------------------------------------------------------------------
def load_and_clean_data(file_path):
    print(">>> 1. Cargando y preprocesando dataset de Domitec...")
    df_raw = pd.read_csv(file_path, sep=';', encoding='latin1', dtype=str)
    
    # Renombrar columnas
    df_raw.columns = [
        'Anio', 'VentasXnegocio', 'Mes', 'Cliente', 'RubroDes',
        'PresentacionDes', 'Pedidos', 'Pendientes', 'Despachadas',
        'Cancelado', 'Pct_Perdida_Vta'
    ]
    
    # Filtrar fila de totales
    df = df_raw[df_raw['Anio'].astype(str).str.strip().str.lower() != 'total'].copy()
    
    # Parser de enteros en formato español (miles con punto)
    def parse_spanish_int(val):
        if pd.isna(val):
            return 0
        val_str = str(val).strip().replace('.', '').replace(',', '.')
        try:
            return int(round(float(val_str)))
        except:
            return 0
            
    def parse_spanish_pct(val):
        if pd.isna(val):
            return 0.0
        val_str = str(val).replace('%', '').replace(',', '.').strip()
        try:
            return float(val_str)
        except:
            return 0.0

    numeric_cols = ['Pedidos', 'Pendientes', 'Despachadas', 'Cancelado']
    for col in numeric_cols:
        df[col] = df[col].apply(parse_spanish_int)
        
    df['Pct_Perdida_Vta_num'] = df['Pct_Perdida_Vta'].apply(parse_spanish_pct)
    
    # Limpieza de textos
    text_cols = ['VentasXnegocio', 'Cliente', 'RubroDes', 'PresentacionDes', 'Mes', 'Anio']
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        
    # Mapeo y consolidación de Productos
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
    
    # Excluir Promopack y Líquido Bactericida
    df = df[df['RubroDes'].isin(rubro_map.keys())].copy()
    df['Producto'] = df['RubroDes'].map(rubro_map)
    
    # Mapeo de Canales Comerciales
    canal_map = {
        'MAXICONSUMO': 'Maxiconsumo',
        'GRANDES CLIENTES': 'Grandes Clientes',
        'RED PROPIA': 'Red Propia'
    }
    df['Canal'] = df['VentasXnegocio'].map(canal_map)
    
    # Mapeo temporal
    meses_map = {
        'Ene.': 1, 'Feb.': 2, 'Mar.': 3, 'Abr.': 4, 'May.': 5, 'Jun.': 6,
        'Jul.': 7, 'Ago.': 8, 'Sept.': 9, 'Oct.': 10, 'Nov.': 11, 'Dic.': 12
    }
    df['Mes_num'] = df['Mes'].map(meses_map)
    df['Anio_num'] = df['Anio'].astype(int)
    df['Periodo'] = df['Anio_num'].astype(str) + '-' + df['Mes_num'].astype(str).str.zfill(2)
    df['Producto_SKU'] = df['Producto'] + " - " + df['PresentacionDes']
    
    periodos_unicos = sorted(df['Periodo'].unique())
    periodo_to_idx = {p: i+1 for i, p in enumerate(periodos_unicos)}
    df['Periodo_Idx'] = df['Periodo'].map(periodo_to_idx)
    
    print(f"    - Registros filtrados incluidos: {len(df):,}")
    print(f"    - Período temporal: {periodos_unicos[0]} a {periodos_unicos[-1]} ({len(periodos_unicos)} meses)")
    print(f"    - Volumen Total Pedido: {df['Pedidos'].sum():,}")
    print(f"    - Volumen Total Despachado: {df['Despachadas'].sum():,}")
    print(f"    - Volumen Total Cancelado: {df['Cancelado'].sum():,}")
    print(f"    - Volumen Total Pendiente: {df['Pendientes'].sum():,}")
    
    return df, periodos_unicos

# ------------------------------------------------------------------------------
# 2. CLASIFICACIÓN Y SEGMENTACIÓN DE CLIENTES
# ------------------------------------------------------------------------------
def analyze_customers(df, total_periodos):
    print("\n>>> 2. Ejecutando Clasificación y Análisis de Clientes...")
    
    cli_summary = df.groupby(['Cliente', 'Canal']).agg(
        Total_Pedidos=('Pedidos', 'sum'),
        Total_Despachadas=('Despachadas', 'sum'),
        Total_Cancelado=('Cancelado', 'sum'),
        Total_Pendientes=('Pendientes', 'sum'),
        Meses_Activos=('Periodo', 'nunique'),
        Lineas_Pedido_Total=('Pedidos', 'count'),
        Cant_SKUs_Distintos=('Producto_SKU', 'nunique')
    ).reset_index()
    
    cli_mensual = df.groupby(['Cliente', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
    
    cli_stats = pd.DataFrame({
        'Media_Mensual': cli_mensual.mean(axis=1),
        'Std_Mensual': cli_mensual.std(axis=1),
        'Min_Mensual': cli_mensual.min(axis=1),
        'Max_Mensual': cli_mensual.max(axis=1),
        'Mediana_Mensual': cli_mensual.median(axis=1)
    }).reset_index()
    
    cli_stats['CV_Demanda'] = np.where(
        cli_stats['Media_Mensual'] > 0,
        cli_stats['Std_Mensual'] / cli_stats['Media_Mensual'],
        0
    )
    
    cli_merged = pd.merge(cli_summary, cli_stats, on='Cliente')
    
    cli_merged['Fill_Rate'] = np.where(
        cli_merged['Total_Pedidos'] > 0,
        cli_merged['Total_Despachadas'] / cli_merged['Total_Pedidos'],
        0.0
    )
    cli_merged['Tasa_Cancelacion'] = np.where(
        cli_merged['Total_Pedidos'] > 0,
        cli_merged['Total_Cancelado'] / cli_merged['Total_Pedidos'],
        0.0
    )
    cli_merged['Frecuencia_Compra_Pct'] = (cli_merged['Meses_Activos'] / len(total_periodos)) * 100
    cli_merged['Ticket_Promedio_Mensual_Activo'] = np.where(
        cli_merged['Meses_Activos'] > 0,
        cli_merged['Total_Pedidos'] / cli_merged['Meses_Activos'],
        0.0
    )
    
    # Clasificación ABC de Clientes
    cli_merged = cli_merged.sort_values(by='Total_Pedidos', ascending=False).reset_index(drop=True)
    cli_merged['Share_Volumen'] = (cli_merged['Total_Pedidos'] / cli_merged['Total_Pedidos'].sum()) * 100
    cli_merged['Share_Acumulado'] = cli_merged['Share_Volumen'].cumsum()
    
    def clasificar_abc(share_acum):
        if share_acum <= 80.0:
            return 'A'
        elif share_acum <= 95.0:
            return 'B'
        else:
            return 'C'
            
    cli_merged['Clase_ABC'] = cli_merged['Share_Acumulado'].apply(clasificar_abc)
    
    def clasificar_estabilidad(cv):
        if cv < 0.5:
            return 'Demanda Estable (Predictible)'
        elif cv < 1.0:
            return 'Demanda Moderada'
        else:
            return 'Demanda Erratica / Volatil'
            
    cli_merged['Tipo_Variabilidad'] = cli_merged['CV_Demanda'].apply(clasificar_estabilidad)
    
    # Recomendación de Roles AnyLogic
    def recomendar_anylogic(row):
        if row['Total_Pedidos'] > 200000 or row['Cliente'] in ['MAXICONSUMO S.A.', 'SUPERMERCADOS MAYORISTAS MAKRO', 'TREOLAND SA']:
            return 'Agente Individual Clave (Key Account Agent)'
        elif row['Clase_ABC'] == 'A' or (row['Canal'] == 'Grandes Clientes'):
            return 'Población Distribuidores Mayores (Individual Wholesaler Agents)'
        elif row['Clase_ABC'] == 'B':
            return 'Población Distribuidores Regionales (Regional Distributor Agents)'
        else:
            return 'Canal Agregado / Población Retailers (Aggregated Minor Retailers)'
            
    cli_merged['Rol_AnyLogic_Recomendado'] = cli_merged.apply(recomendar_anylogic, axis=1)
    cli_merged.to_csv(os.path.join(OUTPUT_DIR, "01_clasificacion_clientes_abc_rfm.csv"), index=False, sep=';', decimal=',')
    
    # Resumen por Canal
    canal_summary = df.groupby('Canal').agg(
        Total_Pedidos=('Pedidos', 'sum'),
        Total_Despachadas=('Despachadas', 'sum'),
        Total_Cancelado=('Cancelado', 'sum'),
        Total_Pendientes=('Pendientes', 'sum'),
        Cantidad_Clientes=('Cliente', 'nunique'),
        Lineas_Transacciones=('Pedidos', 'count')
    ).reset_index()
    
    canal_summary['Share_Pedidos'] = (canal_summary['Total_Pedidos'] / canal_summary['Total_Pedidos'].sum()) * 100
    canal_summary['Fill_Rate'] = (canal_summary['Total_Despachadas'] / canal_summary['Total_Pedidos']) * 100
    canal_summary['Tasa_Cancelacion'] = (canal_summary['Total_Cancelado'] / canal_summary['Total_Pedidos']) * 100
    
    canal_mensual = df.groupby(['Canal', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
    canal_cv = (canal_mensual.std(axis=1) / canal_mensual.mean(axis=1)).reset_index(name='CV_Demanda_Agregada')
    canal_summary = pd.merge(canal_summary, canal_cv, on='Canal')
    canal_summary = canal_summary.sort_values(by='Total_Pedidos', ascending=False)
    canal_summary.to_csv(os.path.join(OUTPUT_DIR, "02_resumen_canales.csv"), index=False, sep=';', decimal=',')
    
    # Concentración
    top1_share = cli_merged.iloc[0]['Share_Volumen']
    top5_share = cli_merged.iloc[:5]['Share_Volumen'].sum()
    top10_share = cli_merged.iloc[:10]['Share_Volumen'].sum()
    hhi = (cli_merged['Share_Volumen'] ** 2).sum()
    
    print("\n--- RESUMEN CLASIFICACIÓN DE CLIENTES ---")
    abc_counts = cli_merged['Clase_ABC'].value_counts()
    for cat in ['A', 'B', 'C']:
        cnt = abc_counts.get(cat, 0)
        vol_pct = cli_merged[cli_merged['Clase_ABC'] == cat]['Share_Volumen'].sum()
        print(f"  Clase {cat}: {cnt:3d} clientes ({cnt/len(cli_merged)*100:5.1f}%) -> {vol_pct:5.1f}% del volumen total")
    print(f"  Concentración HHI: {hhi:.1f}")
    print(f"  Top 1 Share ({cli_merged.iloc[0]['Cliente']}): {top1_share:.2f}%")
    print(f"  Top 5 Share: {top5_share:.2f}% | Top 10 Share: {top10_share:.2f}%")
    
    return cli_merged, canal_summary, cli_mensual

# ------------------------------------------------------------------------------
# 3. AGRUPACIÓN Y CLASIFICACIÓN DE PRODUCTOS (6 FAMILIAS & SKUS)
# ------------------------------------------------------------------------------
def analyze_products(df, total_periodos):
    print("\n>>> 3. Ejecutando Agrupación y Clasificación de Productos (6 Familias Consolidadas)...")
    
    # 3.1 Agrupación por Familia / Producto Consolidado
    prod_summary = df.groupby('Producto').agg(
        Total_Pedidos=('Pedidos', 'sum'),
        Total_Despachadas=('Despachadas', 'sum'),
        Total_Cancelado=('Cancelado', 'sum'),
        Total_Pendientes=('Pendientes', 'sum'),
        Cantidad_Presentaciones=('PresentacionDes', 'nunique'),
        Cantidad_Clientes_Compradores=('Cliente', 'nunique'),
        Lineas_Transacciones=('Pedidos', 'count')
    ).reset_index()
    
    prod_summary['Share_Volumen'] = (prod_summary['Total_Pedidos'] / prod_summary['Total_Pedidos'].sum()) * 100
    prod_summary = prod_summary.sort_values(by='Total_Pedidos', ascending=False).reset_index(drop=True)
    prod_summary['Share_Acumulado'] = prod_summary['Share_Volumen'].cumsum()
    prod_summary['Fill_Rate'] = (prod_summary['Total_Despachadas'] / prod_summary['Total_Pedidos']) * 100
    prod_summary['Tasa_Cancelacion'] = (prod_summary['Total_Cancelado'] / prod_summary['Total_Pedidos']) * 100
    
    prod_mensual = df.groupby(['Producto', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
    prod_cv = (prod_mensual.std(axis=1) / prod_mensual.mean(axis=1)).reset_index(name='CV_Demanda')
    prod_summary = pd.merge(prod_summary, prod_cv, on='Producto')
    
    def abc_prod(acum):
        if acum <= 80.0:
            return 'A'
        elif acum <= 95.0:
            return 'B'
        else:
            return 'C'
    prod_summary['Clase_ABC'] = prod_summary['Share_Acumulado'].apply(abc_prod)
    prod_summary.to_csv(os.path.join(OUTPUT_DIR, "03_agrupacion_rubros.csv"), index=False, sep=';', decimal=',')
    
    # 3.2 Clasificación por SKU (Producto + Presentación)
    sku_summary = df.groupby(['Producto_SKU', 'Producto', 'PresentacionDes']).agg(
        Total_Pedidos=('Pedidos', 'sum'),
        Total_Despachadas=('Despachadas', 'sum'),
        Total_Cancelado=('Cancelado', 'sum'),
        Total_Pendientes=('Pendientes', 'sum'),
        Meses_Con_Venta=('Periodo', 'nunique'),
        Cantidad_Clientes=('Cliente', 'nunique'),
        Lineas_Transacciones=('Pedidos', 'count')
    ).reset_index()
    
    sku_mensual = df.groupby(['Producto_SKU', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
    
    sku_stats = pd.DataFrame({
        'Media_Mensual': sku_mensual.mean(axis=1),
        'Std_Mensual': sku_mensual.std(axis=1),
        'Min_Mensual': sku_mensual.min(axis=1),
        'Max_Mensual': sku_mensual.max(axis=1),
        'Mediana_Mensual': sku_mensual.median(axis=1)
    }).reset_index()
    
    sku_stats['CV_Demanda'] = np.where(
        sku_stats['Media_Mensual'] > 0,
        sku_stats['Std_Mensual'] / sku_stats['Media_Mensual'],
        0
    )
    
    sku_merged = pd.merge(sku_summary, sku_stats, on='Producto_SKU')
    sku_merged = sku_merged.sort_values(by='Total_Pedidos', ascending=False).reset_index(drop=True)
    
    sku_merged['Share_Volumen'] = (sku_merged['Total_Pedidos'] / sku_merged['Total_Pedidos'].sum()) * 100
    sku_merged['Share_Acumulado'] = sku_merged['Share_Volumen'].cumsum()
    sku_merged['Fill_Rate'] = (sku_merged['Total_Despachadas'] / sku_merged['Total_Pedidos']) * 100
    sku_merged['Tasa_Cancelacion'] = (sku_merged['Total_Cancelado'] / sku_merged['Total_Pedidos']) * 100
    
    sku_merged['Clase_ABC'] = sku_merged['Share_Acumulado'].apply(abc_prod)
    
    def clasificar_xyz_sku(cv):
        if cv < 0.25:
            return 'X'
        elif cv < 0.50:
            return 'Y'
        else:
            return 'Z'
    sku_merged['Clase_XYZ'] = sku_merged['CV_Demanda'].apply(clasificar_xyz_sku)
    sku_merged['Matriz_ABC_XYZ'] = sku_merged['Clase_ABC'] + sku_merged['Clase_XYZ']
    
    def recomendar_sku_anylogic(row):
        if row['Matriz_ABC_XYZ'] in ['AX', 'AY'] and row['Share_Volumen'] > 10.0:
            return 'Fase 1: Producto Estrella Principal (Alta Rotación)'
        elif row['Clase_ABC'] in ['A', 'B'] and row['Matriz_ABC_XYZ'] in ['AY', 'BY', 'AZ', 'BZ']:
            return 'Fase 1/2: Producto de Contraste (Media/Alta Rotación con Variabilidad)'
        elif row['PresentacionDes'] in ['3X4.5 LT', '8X2 LT', '3X4 LT'] and row['Clase_ABC'] in ['A', 'B']:
            return 'Fase 2: Presentación Pesada / Mayorista'
        else:
            return 'Fase 3: Catálogo Extendido'
            
    sku_merged['Recomendacion_AnyLogic'] = sku_merged.apply(recomendar_sku_anylogic, axis=1)
    sku_merged.to_csv(os.path.join(OUTPUT_DIR, "04_clasificacion_productos_abc_xyz.csv"), index=False, sep=';', decimal=',')
    
    # Resumen Matriz ABC-XYZ
    matriz_resumen = sku_merged.groupby('Matriz_ABC_XYZ').agg(
        Cantidad_SKUs=('Producto_SKU', 'count'),
        Total_Pedidos=('Total_Pedidos', 'sum'),
        Share_Volumen=('Share_Volumen', 'sum'),
        Fill_Rate_Promedio=('Fill_Rate', 'mean'),
        CV_Promedio=('CV_Demanda', 'mean')
    ).reset_index()
    matriz_resumen.to_csv(os.path.join(OUTPUT_DIR, "05_matriz_abc_xyz_resumen.csv"), index=False, sep=';', decimal=',')
    
    print("\n--- RESUMEN 6 PRODUCTOS CONSOLIDADOS ---")
    for idx, row in prod_summary.iterrows():
        print(f"  {idx+1}. {row['Producto']:<35}: {row['Total_Pedidos']:>10,d} un. ({row['Share_Volumen']:5.1f}%) | Fill Rate: {row['Fill_Rate']:5.1f}% | CV: {row['CV_Demanda']:.3f} | Clase: {row['Clase_ABC']}")
        
    print("\nMatriz ABC-XYZ de SKUs:")
    print(pd.crosstab(sku_merged['Clase_ABC'], sku_merged['Clase_XYZ'], margins=True))
    
    return prod_summary, sku_merged, sku_mensual, prod_mensual

# ------------------------------------------------------------------------------
# 4. PARÁMETROS, SERIES TEMPORALES Y DISTRIBUCIONES PARA ANYLOGIC
# ------------------------------------------------------------------------------
def analyze_anylogic_parameters(df, prod_summary, sku_merged, prod_mensual, sku_mensual):
    print("\n>>> 4. Calculando Parámetros y Distribuciones Estocásticas para AnyLogic...")
    
    # 4.1 Serie Temporal Mensual Global
    serie_mensual = df.groupby('Periodo').agg(
        Pedidos=('Pedidos', 'sum'),
        Despachadas=('Despachadas', 'sum'),
        Cancelado=('Cancelado', 'sum'),
        Pendientes=('Pendientes', 'sum'),
        Lineas_Totales=('Pedidos', 'count')
    ).reset_index()
    
    serie_mensual['Fill_Rate'] = (serie_mensual['Despachadas'] / serie_mensual['Pedidos']) * 100
    serie_mensual['Tasa_Cancelacion'] = (serie_mensual['Cancelado'] / serie_mensual['Pedidos']) * 100
    serie_mensual.to_csv(os.path.join(OUTPUT_DIR, "06_serie_temporal_mensual.csv"), index=False, sep=';', decimal=',')
    
    # 4.2 Ajuste de Distribuciones de Demanda para los 6 Productos Consolidados y Demanda Global
    fit_results = []
    
    demanda_global_mensual = serie_mensual['Pedidos'].values
    mu_g, std_g = float(np.mean(demanda_global_mensual)), float(np.std(demanda_global_mensual, ddof=1))
    fit_results.append({
        'Entidad': 'DEMANDA TOTAL PLANTA (6 PRODUCTOS)',
        'Tipo': 'Total Fábrica',
        'Media_u': mu_g,
        'Std_s': std_g,
        'CV': std_g / mu_g,
        'Min': float(np.min(demanda_global_mensual)),
        'Max': float(np.max(demanda_global_mensual)),
        'Mediana': float(np.median(demanda_global_mensual)),
        'Mejor_Distribucion': 'Normal / Triangular',
        'Sintaxis_AnyLogic_Normal': f"normal({mu_g:.1f}, {std_g:.1f})",
        'Sintaxis_AnyLogic_Triangular': f"triangular({np.min(demanda_global_mensual):.1f}, {np.median(demanda_global_mensual):.1f}, {np.max(demanda_global_mensual):.1f})",
        'Capacidad_Mensual_Sugerida_85pct': f"{mu_g * 1.15:,.0f} un/mes"
    })
    
    for prod in prod_summary['Producto'].tolist():
        serie_p = prod_mensual.loc[prod].values
        mu = float(np.mean(serie_p))
        std = float(np.std(serie_p, ddof=1)) if len(serie_p) > 1 else 0.0
        cv = std / mu if mu > 0 else 0.0
        min_v = float(np.min(serie_p))
        max_v = float(np.max(serie_p))
        med_v = float(np.median(serie_p))
        
        ks_norm = stats.kstest(serie_p, stats.norm(loc=mu, scale=std).cdf).pvalue if std > 0 else 0.0
        best_dist = 'Normal' if ks_norm > 0.05 else 'Triangular / Lognormal'
        
        fit_results.append({
            'Entidad': prod,
            'Tipo': 'Familia Consolidada',
            'Media_u': mu,
            'Std_s': std,
            'CV': cv,
            'Min': min_v,
            'Max': max_v,
            'Mediana': med_v,
            'Mejor_Distribucion': best_dist,
            'Sintaxis_AnyLogic_Normal': f"normal({mu:.1f}, {std:.1f})",
            'Sintaxis_AnyLogic_Triangular': f"triangular({min_v:.1f}, {med_v:.1f}, {max_v:.1f})",
            'Capacidad_Mensual_Sugerida_85pct': f"{mu * 1.15:,.0f} un/mes"
        })
        
    df_fits = pd.DataFrame(fit_results)
    df_fits.to_csv(os.path.join(OUTPUT_DIR, "07_ajuste_distribuciones_anylogic.csv"), index=False, sep=';', decimal=',')
    
    # 4.3 Mix Canal x Producto
    mix_canal = df.groupby(['Canal', 'Producto'])['Pedidos'].sum().unstack(fill_value=0)
    mix_canal_pct = mix_canal.div(mix_canal.sum(axis=1), axis=0) * 100
    mix_canal_pct.to_csv(os.path.join(OUTPUT_DIR, "08_mix_canal_producto.csv"), sep=';', decimal=',')
    
    return serie_mensual, df_fits, mix_canal_pct

# ------------------------------------------------------------------------------
# 5. GENERACIÓN DE GRÁFICOS VISUALES
# ------------------------------------------------------------------------------
def generate_charts(df, cli_merged, canal_summary, prod_summary, sku_merged, serie_mensual, prod_mensual):
    print("\n>>> 5. Generando Gráficos de Alta Calidad...")
    
    # 5.1 Pareto de Clientes
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
    x = range(1, len(cli_merged) + 1)
    y_vol = cli_merged['Share_Volumen']
    y_cum = cli_merged['Share_Acumulado']
    
    ax1.bar(x[:30], y_vol[:30], color='#1f77b4', alpha=0.8, label='% Volumen por Cliente (Top 30)')
    ax1.set_xlabel('Ranking de Clientes', fontsize=11, fontweight='bold')
    ax1.set_ylabel('% Volumen Individual', color='#1f77b4', fontsize=11, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    
    ax2 = ax1.twinx()
    ax2.plot(x, y_cum, color='#d62728', linewidth=2.5, label='% Volumen Acumulado')
    ax2.axhline(80, color='gray', linestyle='--', alpha=0.7, label='Límite 80% (Clase A)')
    ax2.axhline(95, color='orange', linestyle=':', alpha=0.7, label='Límite 95% (Clase B)')
    ax2.set_ylabel('% Volumen Acumulado', color='#d62728', fontsize=11, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#d62728')
    ax2.set_ylim(0, 105)
    
    plt.title('Curva de Pareto de Clientes - Domitec S.A. (Demanda 2025-2026)', fontsize=13, fontweight='bold', pad=15)
    plt.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "01_pareto_clientes.png"), dpi=300)
    plt.close()
    
    # 5.2 Pareto de Productos Consolidados
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
    x_pos = range(len(prod_summary))
    labels = prod_summary['Producto'].tolist()
    
    ax1.bar(x_pos, prod_summary['Total_Pedidos'] / 1000, color='#2ca02c', alpha=0.85, width=0.55)
    ax1.set_ylabel('Miles de Unidades Pedidas', color='#2ca02c', fontsize=11, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([l.replace(' / ', '\n') for l in labels], rotation=25, ha='right', fontsize=9, fontweight='bold')
    
    ax2 = ax1.twinx()
    ax2.plot(x_pos, prod_summary['Share_Acumulado'], color='#d62728', marker='o', linewidth=2.5)
    ax2.axhline(80, color='gray', linestyle='--', label='Corte 80% (Clase A)')
    ax2.set_ylabel('% Acumulado', color='#d62728', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, 105)
    
    plt.title('Concentración de Demanda por Familias de Productos (6 Consolidadas)', fontsize=13, fontweight='bold', pad=15)
    fig.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "02_pareto_productos.png"), dpi=300)
    plt.close()
    
    # 5.3 Matriz ABC-XYZ Scatter Plot de SKUs
    plt.figure(figsize=(10, 6), dpi=300)
    colors = {'A': '#d62728', 'B': '#ff7f0e', 'C': '#1f77b4'}
    for clase, grp in sku_merged.groupby('Clase_ABC'):
        plt.scatter(grp['CV_Demanda'], grp['Total_Pedidos'] / 1000, 
                    s=grp['Share_Volumen']*35 + 40, 
                    color=colors[clase], alpha=0.7, edgecolors='black', label=f'Clase {clase}')
        
    for _, row in sku_merged.head(8).iterrows():
        plt.annotate(row['Producto_SKU'].split(' - ')[0][:12] + ' (' + row['PresentacionDes'] + ')',
                     (row['CV_Demanda'], row['Total_Pedidos'] / 1000),
                     xytext=(5, 5), textcoords='offset points', fontsize=7.5, fontweight='bold')
                     
    plt.axvline(0.25, color='gray', linestyle='--', alpha=0.7)
    plt.axvline(0.50, color='gray', linestyle='--', alpha=0.7)
    plt.text(0.12, plt.ylim()[1]*0.9, 'ZONA X\n(Estable)', color='darkgreen', fontweight='bold', ha='center')
    plt.text(0.37, plt.ylim()[1]*0.9, 'ZONA Y\n(Moderada)', color='darkorange', fontweight='bold', ha='center')
    plt.text(0.75, plt.ylim()[1]*0.9, 'ZONA Z\n(Errática)', color='darkred', fontweight='bold', ha='center')
    
    plt.xlabel('Coeficiente de Variación (CV = σ / μ)', fontsize=11, fontweight='bold')
    plt.ylabel('Volumen Total Pedido (Miles de Unidades)', fontsize=11, fontweight='bold')
    plt.title('Matriz ABC - XYZ de SKUs Domitec (Catálogo Actualizado)', fontsize=13, fontweight='bold', pad=15)
    plt.legend(title='Clasificación ABC', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "03_matriz_abc_xyz.png"), dpi=300)
    plt.close()
    
    # 5.4 Serie Temporal de Demanda, Despacho y Fill Rate
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, dpi=300, gridspec_kw={'height_ratios': [2, 1]})
    
    x_per = serie_mensual['Periodo']
    ax1.plot(x_per, serie_mensual['Pedidos'] / 1000, marker='o', color='#1f77b4', linewidth=2.2, label='Pedidos Totales')
    ax1.plot(x_per, serie_mensual['Despachadas'] / 1000, marker='s', color='#2ca02c', linewidth=2, label='Despachadas')
    ax1.plot(x_per, serie_mensual['Cancelado'] / 1000, marker='^', color='#d62728', linewidth=1.8, linestyle='--', label='Cancelado')
    ax1.set_ylabel('Miles de Unidades', fontsize=11, fontweight='bold')
    ax1.set_title('Evolución Temporal de Demanda y Cumplimiento Mensual (2025 - 2026)', fontsize=13, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    avg_fill_rate = (serie_mensual['Despachadas'].sum() / serie_mensual['Pedidos'].sum()) * 100
    ax2.plot(x_per, serie_mensual['Fill_Rate'], marker='d', color='#9467bd', linewidth=2, label=f'Fill Rate Real (%)')
    ax2.axhline(avg_fill_rate, color='red', linestyle=':', label=f'Fill Rate Promedio ({avg_fill_rate:.1f}%)')
    ax2.set_ylabel('Fill Rate (%)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Período (Año-Mes)', fontsize=11, fontweight='bold')
    ax2.set_ylim(60, 100)
    ax2.set_xticks(range(len(x_per)))
    ax2.set_xticklabels(x_per, rotation=45, ha='right', fontsize=9)
    ax2.legend(loc='lower right')
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    fig.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "04_serie_temporal_demanda_y_fillrate.png"), dpi=300)
    plt.close()
    
    # 5.5 Demanda Mensual por las 6 Familias Consolidadas
    plt.figure(figsize=(12, 6), dpi=300)
    for prod in prod_summary['Producto'].tolist():
        plt.plot(prod_mensual.columns, prod_mensual.loc[prod] / 1000, marker='o', linewidth=2, label=prod)
        
    plt.title('Evolución Mensual de Demanda por Familias de Productos (6 Consolidadas)', fontsize=13, fontweight='bold', pad=15)
    plt.xlabel('Período (Año-Mes)', fontsize=11, fontweight='bold')
    plt.ylabel('Miles de Unidades Pedidas', fontsize=11, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.legend(title='Producto', loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "05_demanda_por_rubro_mensual.png"), dpi=300)
    plt.close()
    
    # 5.6 Variabilidad de Demanda por Canal (Efecto Látigo / Agregación)
    plt.figure(figsize=(9, 5), dpi=300)
    canal_mensual_df = df.groupby(['Periodo', 'Canal'])['Pedidos'].sum().unstack(fill_value=0)
    cv_canales = (canal_mensual_df.std() / canal_mensual_df.mean()).sort_values()
    
    bars = plt.bar(cv_canales.index, cv_canales.values, color=['#2ca02c', '#ff7f0e', '#d62728'], width=0.5, alpha=0.85)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01, f"CV = {yval:.3f}", ha='center', va='bottom', fontweight='bold')
        
    plt.title('Variabilidad de Demanda por Canal Comercial (Coeficiente de Variación CV)', fontsize=12, fontweight='bold', pad=15)
    plt.ylabel('CV = Desv. Estándar / Media', fontsize=11, fontweight='bold')
    plt.ylim(0, max(cv_canales.values) * 1.25)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "06_comparacion_variabilidad_canales.png"), dpi=300)
    plt.close()
    
    print("    -> Gráficos generados exitosamente en:", CHARTS_DIR)

# ------------------------------------------------------------------------------
# 6. FUNCIÓN PRINCIPAL
# ------------------------------------------------------------------------------
def main():
    print("=" * 80)
    print(" INICIANDO ANÁLISIS DE DEMANDA PARA SIMULACIÓN EN ANYLOGIC - DOMITEC S.A.")
    print("=" * 80)
    
    df, periodos_unicos = load_and_clean_data(DATA_PATH)
    cli_merged, canal_summary, cli_mensual = analyze_customers(df, periodos_unicos)
    prod_summary, sku_merged, sku_mensual, prod_mensual = analyze_products(df, periodos_unicos)
    serie_mensual, df_fits, mix_canal_pct = analyze_anylogic_parameters(df, prod_summary, sku_merged, prod_mensual, sku_mensual)
    generate_charts(df, cli_merged, canal_summary, prod_summary, sku_merged, serie_mensual, prod_mensual)
    
    print("\n" + "=" * 80)
    print(" ANÁLISIS COMPLETADO EXITOSAMENTE.")
    print(f" Archivos generados en: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == '__main__':
    main()
