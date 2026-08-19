"""
================================================================================
ANÁLISIS DE DEMANDA - DOMITEC S.A.
PROYECTO DE SIMULACIÓN EN ANYLOGIC (EFECTO LÁTIGO & CADENA DE SUMINISTRO)
================================================================================
Este script realiza el análisis integral de demanda a partir de los datos reales
de Domitec (2025 - 2026), con los siguientes objetivos:
1. Clasificar y segmentar clientes (ABC, RFM, Variabilidad, Concentración, Nivel de Servicio).
2. Agrupar y clasificar productos (Rubros, ABC, XYZ por variabilidad, Matriz ABC-XYZ).
3. Obtener métricas clave para AnyLogic (Ajuste de distribuciones estocásticas,
   análisis de variabilidad por canal / efecto látigo, estacionalidad y capacidad).
4. Generar reportes CSV y gráficos visuales de alta calidad.
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

# Configuración de estilo de visualización
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
    text_cols = ['VentasXnegocio', 'Cliente', 'RubroDes', 'PresentacionDes', 'Mes']
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        
    # Mapeo temporal
    meses_map = {
        'Ene.': 1, 'Feb.': 2, 'Mar.': 3, 'Abr.': 4, 'May.': 5, 'Jun.': 6,
        'Jul.': 7, 'Ago.': 8, 'Sept.': 9, 'Oct.': 10, 'Nov.': 11, 'Dic.': 12
    }
    df['Mes_num'] = df['Mes'].map(meses_map)
    df['Anio_num'] = df['Anio'].astype(int)
    df['Periodo'] = df['Anio_num'].astype(str) + '-' + df['Mes_num'].astype(str).str.zfill(2)
    df['Producto_SKU'] = df['RubroDes'] + " - " + df['PresentacionDes']
    
    # Crear un índice cronológico ordenado (1 a 20)
    periodos_unicos = sorted(df['Periodo'].unique())
    periodo_to_idx = {p: i+1 for i, p in enumerate(periodos_unicos)}
    df['Periodo_Idx'] = df['Periodo'].map(periodo_to_idx)
    
    print(f"    - Registros cargados: {len(df):,}")
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
    
    # Agregación por Cliente y Canal
    cli_summary = df.groupby(['Cliente', 'VentasXnegocio']).agg(
        Total_Pedidos=('Pedidos', 'sum'),
        Total_Despachadas=('Despachadas', 'sum'),
        Total_Cancelado=('Cancelado', 'sum'),
        Total_Pendientes=('Pendientes', 'sum'),
        Meses_Activos=('Periodo', 'nunique'),
        Lineas_Pedido_Total=('Pedidos', 'count'),
        Cant_SKUs_Distintos=('Producto_SKU', 'nunique')
    ).reset_index()
    
    # Métricas mensuales por cliente para variabilidad (CV)
    cli_mensual = df.groupby(['Cliente', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
    
    # Calcular métricas estadísticas mensuales por cliente sobre los 20 meses
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
    
    # Métricas de Servicio
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
    
    # Clasificación ABC por Volumen de Pedidos
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
    
    # Clasificación de Estabilidad de Demanda (Regularidad)
    def clasificar_estabilidad(cv):
        if cv < 0.5:
            return 'Demanda Estable (Predictible)'
        elif cv < 1.0:
            return 'Demanda Moderada'
        else:
            return 'Demanda Erratica / Volatil'
            
    cli_merged['Tipo_Variabilidad'] = cli_merged['CV_Demanda'].apply(clasificar_estabilidad)
    
    # Recomendación AnyLogic
    def recomendar_anylogic(row):
        if row['Total_Pedidos'] > 200000 or row['Cliente'] in ['MAXICONSUMO S.A.', 'SUPERMERCADOS MAYORISTAS MAKRO', 'TREOLAND SA']:
            return 'Agente Individual Clave (Key Account Agent)'
        elif row['Clase_ABC'] == 'A' or (row['VentasXnegocio'] == 'GRANDES CLIENTES'):
            return 'Población Distribuidores Mayores (Individual Wholesaler Agents)'
        elif row['Clase_ABC'] == 'B':
            return 'Población Distribuidores Regionales (Regional Distributor Agents)'
        else:
            return 'Canal Agregado / Población Retailers (Aggregated Minor Retailers)'
            
    cli_merged['Rol_AnyLogic_Recomendado'] = cli_merged.apply(recomendar_anylogic, axis=1)
    
    # Guardar reporte
    cli_merged.to_csv(os.path.join(OUTPUT_DIR, "01_clasificacion_clientes_abc_rfm.csv"), index=False, sep=';', decimal=',')
    
    # Resumen por Canal de Venta
    canal_summary = df.groupby('VentasXnegocio').agg(
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
    
    # Variabilidad agregada por canal mes a mes
    canal_mensual = df.groupby(['VentasXnegocio', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
    canal_cv = (canal_mensual.std(axis=1) / canal_mensual.mean(axis=1)).reset_index(name='CV_Demanda_Agregada')
    canal_summary = pd.merge(canal_summary, canal_cv, on='VentasXnegocio')
    canal_summary.to_csv(os.path.join(OUTPUT_DIR, "02_resumen_canales.csv"), index=False, sep=';', decimal=',')
    
    # Métricas de Concentración
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
    print(f"  Concentración HHI: {hhi:.1f} (Altamente concentrado > 1500)")
    print(f"  Top 1 Share ({cli_merged.iloc[0]['Cliente']}): {top1_share:.2f}%")
    print(f"  Top 5 Share: {top5_share:.2f}% | Top 10 Share: {top10_share:.2f}%")
    
    return cli_merged, canal_summary, cli_mensual

# ------------------------------------------------------------------------------
# 3. AGRUPACIÓN Y CLASIFICACIÓN DE PRODUCTOS
# ------------------------------------------------------------------------------
def analyze_products(df, total_periodos):
    print("\n>>> 3. Ejecutando Agrupación y Clasificación de Productos...")
    
    # 3.1 Agrupación por Rubro (Familia)
    rubro_summary = df.groupby('RubroDes').agg(
        Total_Pedidos=('Pedidos', 'sum'),
        Total_Despachadas=('Despachadas', 'sum'),
        Total_Cancelado=('Cancelado', 'sum'),
        Total_Pendientes=('Pendientes', 'sum'),
        Cantidad_Presentaciones=('PresentacionDes', 'nunique'),
        Cantidad_Clientes_Compradores=('Cliente', 'nunique'),
        Lineas_Transacciones=('Pedidos', 'count')
    ).reset_index()
    
    rubro_summary['Share_Volumen'] = (rubro_summary['Total_Pedidos'] / rubro_summary['Total_Pedidos'].sum()) * 100
    rubro_summary = rubro_summary.sort_values(by='Total_Pedidos', ascending=False).reset_index(drop=True)
    rubro_summary['Share_Acumulado'] = rubro_summary['Share_Volumen'].cumsum()
    rubro_summary['Fill_Rate'] = (rubro_summary['Total_Despachadas'] / rubro_summary['Total_Pedidos']) * 100
    rubro_summary['Tasa_Cancelacion'] = (rubro_summary['Total_Cancelado'] / rubro_summary['Total_Pedidos']) * 100
    
    # Variabilidad mensual por rubro
    rubro_mensual = df.groupby(['RubroDes', 'Periodo'])['Pedidos'].sum().unstack(fill_value=0)
    rubro_cv = (rubro_mensual.std(axis=1) / rubro_mensual.mean(axis=1)).reset_index(name='CV_Demanda')
    rubro_summary = pd.merge(rubro_summary, rubro_cv, on='RubroDes')
    rubro_summary.to_csv(os.path.join(OUTPUT_DIR, "03_agrupacion_rubros.csv"), index=False, sep=';', decimal=',')
    
    # 3.2 Clasificación por SKU (Rubro + Presentación)
    sku_summary = df.groupby(['Producto_SKU', 'RubroDes', 'PresentacionDes']).agg(
        Total_Pedidos=('Pedidos', 'sum'),
        Total_Despachadas=('Despachadas', 'sum'),
        Total_Cancelado=('Cancelado', 'sum'),
        Total_Pendientes=('Pendientes', 'sum'),
        Meses_Con_Venta=('Periodo', 'nunique'),
        Cantidad_Clientes=('Cliente', 'nunique'),
        Lineas_Transacciones=('Pedidos', 'count')
    ).reset_index()
    
    # Variabilidad mensual por SKU
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
    
    # Clasificación ABC de Productos
    def clasificar_abc_sku(share_acum):
        if share_acum <= 80.0:
            return 'A'
        elif share_acum <= 95.0:
            return 'B'
        else:
            return 'C'
    sku_merged['Clase_ABC'] = sku_merged['Share_Acumulado'].apply(clasificar_abc_sku)
    
    # Clasificación XYZ de Productos (Variabilidad)
    def clasificar_xyz_sku(cv):
        if cv < 0.25:
            return 'X'  # Muy estable / flujo constante
        elif cv < 0.50:
            return 'Y'  # Moderadamente variable
        else:
            return 'Z'  # Alta variabilidad o estacionalidad
    sku_merged['Clase_XYZ'] = sku_merged['CV_Demanda'].apply(clasificar_xyz_sku)
    sku_merged['Matriz_ABC_XYZ'] = sku_merged['Clase_ABC'] + sku_merged['Clase_XYZ']
    
    # Recomendación para AnyLogic
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
    
    print("\n--- RESUMEN CLASIFICACIÓN DE PRODUCTOS ---")
    print(f"Total Rubros: {len(rubro_summary)} | Total SKUs: {len(sku_merged)}")
    print("\nTop 5 Rubros por Volumen:")
    for idx, row in rubro_summary.head(5).iterrows():
        print(f"  {idx+1}. {row['RubroDes']:<25}: {row['Total_Pedidos']:>10,d} un. ({row['Share_Volumen']:5.1f}%) | Fill Rate: {row['Fill_Rate']:5.1f}% | CV: {row['CV_Demanda']:.2f}")
        
    print("\nMatriz ABC-XYZ de Productos (Distribución de SKUs):")
    print(pd.crosstab(sku_merged['Clase_ABC'], sku_merged['Clase_XYZ'], margins=True))
    
    return rubro_summary, sku_merged, sku_mensual

# ------------------------------------------------------------------------------
# 4. MÉTRICAS CLAVE, SERIES TEMPORALES Y AJUSTE DE DISTRIBUCIONES PARA ANYLOGIC
# ------------------------------------------------------------------------------
def analyze_anylogic_parameters(df, sku_merged, sku_mensual):
    print("\n>>> 4. Calculando Parámetros y Distribuciones Estocásticas para AnyLogic...")
    
    # 4.1 Serie Temporal Total Mensual
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
    
    # 4.2 Ajuste de Distribuciones de Demanda para SKUs Clave y Demanda Global
    # Seleccionar top SKUs y demanda global
    top_skus = sku_merged.head(6)['Producto_SKU'].tolist()
    
    fit_results = []
    
    # Analizar demanda mensual global
    demanda_global_mensual = serie_mensual['Pedidos'].values
    mu_g, std_g = np.mean(demanda_global_mensual), np.std(demanda_global_mensual, ddof=1)
    fit_results.append({
        'Entidad': 'DEMANDA TOTAL PLANTA',
        'Nivel': 'Mensual Global',
        'Media_u': mu_g,
        'Std_s': std_g,
        'CV': std_g / mu_g,
        'Min': np.min(demanda_global_mensual),
        'Max': np.max(demanda_global_mensual),
        'Mediana': np.median(demanda_global_mensual),
        'Mejor_Distribucion': 'Normal / Triangular',
        'Sintaxis_AnyLogic_Normal': f"normal({mu_g:.1f}, {std_g:.1f})",
        'Sintaxis_AnyLogic_Triangular': f"triangular({np.min(demanda_global_mensual):.1f}, {np.median(demanda_global_mensual):.1f}, {np.max(demanda_global_mensual):.1f})",
        'Capacidad_Mensual_Sugerida_85pct': f"{mu_g * 1.15:,.0f} un/mes"
    })
    
    # Analizar cada top SKU a nivel mensual
    for sku in top_skus:
        sku_row = sku_merged[sku_merged['Producto_SKU'] == sku].iloc[0]
        serie_sku = sku_mensual.loc[sku].values
        mu = np.mean(serie_sku)
        std = np.std(serie_sku, ddof=1) if len(serie_sku) > 1 else 0
        cv = std / mu if mu > 0 else 0
        min_v = np.min(serie_sku)
        max_v = np.max(serie_sku)
        med_v = np.median(serie_sku)
        
        # Test Kolmogorov-Smirnov contra normal y lognormal
        ks_norm = stats.kstest(serie_sku, 'norm', args=(mu, std))[1] if std > 0 else 0
        
        best_dist = 'Normal' if ks_norm > 0.05 else 'Triangular / Lognormal'
        
        fit_results.append({
            'Entidad': sku,
            'Nivel': f"Mensual SKU ({sku_row['Matriz_ABC_XYZ']})",
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
    mix_canal = df.groupby(['VentasXnegocio', 'RubroDes'])['Pedidos'].sum().unstack(fill_value=0)
    mix_canal_pct = mix_canal.div(mix_canal.sum(axis=1), axis=0) * 100
    mix_canal_pct.to_csv(os.path.join(OUTPUT_DIR, "08_mix_canal_producto.csv"), sep=';', decimal=',')
    
    return serie_mensual, df_fits, mix_canal_pct

# ------------------------------------------------------------------------------
# 5. GENERACIÓN DE GRÁFICOS VISUALES
# ------------------------------------------------------------------------------
def generate_charts(df, cli_merged, canal_summary, rubro_summary, sku_merged, serie_mensual, sku_mensual):
    print("\n>>> 5. Generando Gráficos de Alta Calidad...")
    
    # 5.1 Pareto de Clientes
    plt.figure(figsize=(10, 6), dpi=300)
    fig, ax1 = plt.subplots(figsize=(10, 6))
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
    
    # 5.2 Pareto de Productos (SKUs)
    fig, ax1 = plt.subplots(figsize=(11, 6), dpi=300)
    top_skus_df = sku_merged.head(15)
    x_labels = [s.replace(' - ', '\n') for s in top_skus_df['Producto_SKU']]
    
    ax1.bar(range(len(top_skus_df)), top_skus_df['Total_Pedidos'] / 1000, color='#2ca02c', alpha=0.85, width=0.6)
    ax1.set_ylabel('Miles de Unidades Pedidas', color='#2ca02c', fontsize=11, fontweight='bold')
    ax1.set_xticks(range(len(top_skus_df)))
    ax1.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=8)
    
    ax2 = ax1.twinx()
    ax2.plot(range(len(top_skus_df)), top_skus_df['Share_Acumulado'], color='#d62728', marker='o', linewidth=2)
    ax2.axhline(80, color='gray', linestyle='--', label='Corte 80% (Clase A)')
    ax2.set_ylabel('% Acumulado', color='#d62728', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, 105)
    
    plt.title('Top 15 Productos (SKUs) y Curva de Concentración Pareto', fontsize=13, fontweight='bold', pad=15)
    fig.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "02_pareto_productos.png"), dpi=300)
    plt.close()
    
    # 5.3 Matriz ABC-XYZ Scatter Plot
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
    plt.title('Matriz ABC - XYZ de Productos Domitec', fontsize=13, fontweight='bold', pad=15)
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
    ax1.set_title('Evolución Temporal de la Demanda y Cumplimiento Mensual (2025 - 2026)', fontsize=13, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    ax2.plot(x_per, serie_mensual['Fill_Rate'], marker='d', color='#9467bd', linewidth=2, label='Fill Rate Real (%)')
    ax2.axhline(85.7, color='red', linestyle=':', label='Fill Rate Promedio (85.7%)')
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
    
    # 5.5 Demanda Mensual por Rubro Principal
    plt.figure(figsize=(12, 6), dpi=300)
    top_rubros = rubro_summary.head(5)['RubroDes'].tolist()
    rubro_mensual_df = df[df['RubroDes'].isin(top_rubros)].groupby(['Periodo', 'RubroDes'])['Pedidos'].sum().unstack(fill_value=0)
    
    for rub in top_rubros:
        plt.plot(rubro_mensual_df.index, rubro_mensual_df[rub] / 1000, marker='o', linewidth=2, label=rub)
        
    plt.title('Evolución Mensual de Demanda por Rubro Principal', fontsize=13, fontweight='bold', pad=15)
    plt.xlabel('Período (Año-Mes)', fontsize=11, fontweight='bold')
    plt.ylabel('Miles de Unidades Pedidas', fontsize=11, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.legend(title='Rubro', loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "05_demanda_por_rubro_mensual.png"), dpi=300)
    plt.close()
    
    # 5.6 Variabilidad de la Demanda por Canal (Efecto Látigo / Agregación)
    plt.figure(figsize=(9, 5), dpi=300)
    canal_mensual_df = df.groupby(['Periodo', 'VentasXnegocio'])['Pedidos'].sum().unstack(fill_value=0)
    cv_canales = (canal_mensual_df.std() / canal_mensual_df.mean()).sort_values()
    
    bars = plt.bar(cv_canales.index, cv_canales.values, color=['#2ca02c', '#ff7f0e', '#d62728'], width=0.5, alpha=0.85)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01, f"CV = {yval:.3f}", ha='center', va='bottom', fontweight='bold')
        
    plt.title('Variabilidad de la Demanda por Canal Comercial (Coeficiente de Variación CV)', fontsize=12, fontweight='bold', pad=15)
    plt.ylabel('CV = Desv. Estándar / Media', fontsize=11, fontweight='bold')
    plt.ylim(0, max(cv_canales.values) * 1.25)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "06_comparacion_variabilidad_canales.png"), dpi=300)
    plt.close()
    
    print("    -> Todos los gráficos fueron generados exitosamente en:", CHARTS_DIR)

# ------------------------------------------------------------------------------
# 6. FUNCIÓN PRINCIPAL
# ------------------------------------------------------------------------------
def main():
    print("=" * 80)
    print(" INICIANDO ANÁLISIS DE DEMANDA PARA SIMULACIÓN EN ANYLOGIC - DOMITEC S.A.")
    print("=" * 80)
    
    df, periodos_unicos = load_and_clean_data(DATA_PATH)
    cli_merged, canal_summary, cli_mensual = analyze_customers(df, periodos_unicos)
    rubro_summary, sku_merged, sku_mensual = analyze_products(df, periodos_unicos)
    serie_mensual, df_fits, mix_canal_pct = analyze_anylogic_parameters(df, sku_merged, sku_mensual)
    generate_charts(df, cli_merged, canal_summary, rubro_summary, sku_merged, serie_mensual, sku_mensual)
    
    print("\n" + "=" * 80)
    print(" ANÁLISIS COMPLETADO EXITOSAMENTE.")
    print(f" Archivos generados en: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == '__main__':
    main()
