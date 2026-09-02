# Análisis de Demanda y Parámetros de Simulación - Domitec S.A.

Este documento contiene la información procesada y los parámetros estadísticos requeridos para el modelo de simulación en **AnyLogic** de la cadena de suministro y efecto látigo de **Domitec S.A.** (20 meses históricos: enero 2025 – agosto 2026).

---

## 1. Alcance y Catálogo de Productos

El catálogo activo para la simulación se compone estrictamente de **6 productos consolidados**:

1. **Lavandina**: Unificación de *Lavandina Común* y *Lavandina Concentrada*.
2. **Líquido Desinfectante**: Unificación de *Líquido Desinfectante* y *Líquido Limpiador*.
3. **Lavavajilla**
4. **Líquido Lavar Ropa**
5. **Suavizante**
6. **Detergente Concentrado**

> [!NOTE]
> Los productos *Promopack* y *Líquido Bactericida* fueron excluidos. El volumen total demandado analizado es de **5.496.539 unidades** (promedio mensual total de **274.827 unidades/mes**).

---

## 2. Resumen General por Producto

| # | Producto | Pedidos Totales (20 Meses) | Share Demanda (%) | Media Mensual ($\mu$) | Desv. Estándar ($s$) | Coef. Variación ($CV$) | Nivel de Servicio (Fill Rate) |
| :-: | :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | **Lavandina** | 2.102.504 un. | 38,25% | 105.125,2 un. | 29.041,3 un. | 0,276 | 90,06% |
| 2 | **Líquido Desinfectante** | 1.401.534 un. | 25,50% | 70.076,7 un. | 21.967,0 un. | 0,313 | 80,61% |
| 3 | **Lavavajilla** | 1.020.841 un. | 18,57% | 51.042,1 un. | 15.414,9 un. | 0,302 | 87,30% |
| 4 | **Líquido Lavar Ropa** | 434.161 un. | 7,90% | 21.708,1 un. | 9.296,4 un. | 0,428 | 81,29% |
| 5 | **Suavizante** | 360.281 un. | 6,55% | 18.014,1 un. | 5.378,0 un. | 0,299 | 79,53% |
| 6 | **Detergente Concentrado** | 177.218 un. | 3,22% | 8.860,9 un. | 4.521,2 un. | 0,510 | 86,78% |
| - | **TOTAL PLANTA** | **5.496.539 un.** | **100,00%** | **274.827,0 un.** | **60.834,1 un.** | **0,221** | **85,65%** |

---

## 3. Demanda Mensual para AnyLogic por Canal y Producto (18 Perfiles)

Parámetros calculados sobre los 20 períodos para programar los generadores de demanda de los 3 segmentos de clientes (**Maxiconsumo**, **Grandes Clientes** y **Red Propia**):

| Perfil de Cliente | Producto | Media Mensual ($\mu$) | Desv. Est. Pob. ($\sigma$) | Desv. Est. Muestral ($s$) | CV Demanda | Total Demandado (20 Meses) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Maxiconsumo** | Lavandina | 37.515,80 | 21.758,34 | 22.323,58 | 0,5800 | 750.316 un. |
| **Maxiconsumo** | Líquido Desinfectante | 24.685,75 | 16.016,04 | 16.432,11 | 0,6488 | 493.715 un. |
| **Maxiconsumo** | Lavavajilla | 20.414,40 | 11.803,80 | 12.110,44 | 0,5782 | 408.288 un. |
| **Maxiconsumo** | Líquido Lavar Ropa | 8.735,35 | 6.992,12 | 7.173,76 | 0,8004 | 174.707 un. |
| **Maxiconsumo** | Suavizante | 7.061,90 | 4.577,44 | 4.696,36 | 0,6482 | 141.238 un. |
| **Maxiconsumo** | Detergente Concentrado | 4.182,95 | 3.557,61 | 3.650,03 | 0,8505 | 83.659 un. |
| **Grandes Clientes** | Lavandina | 12.293,90 | 5.195,27 | 5.330,24 | 0,4226 | 245.878 un. |
| **Grandes Clientes** | Líquido Desinfectante | 18.271,05 | 10.749,78 | 11.029,05 | 0,5884 | 365.421 un. |
| **Grandes Clientes** | Lavavajilla | 8.325,95 | 4.317,54 | 4.429,70 | 0,5186 | 166.519 un. |
| **Grandes Clientes** | Líquido Lavar Ropa | 1.249,50 | 940,44 | 964,87 | 0,7527 | 24.990 un. |
| **Grandes Clientes** | Suavizante | 2.064,95 | 1.577,46 | 1.618,44 | 0,7639 | 41.299 un. |
| **Grandes Clientes** | Detergente Concentrado | 0,00 | 0,00 | 0,00 | 0,0000 | 0 un. |
| **Red Propia** | Lavandina | 55.315,50 | 13.159,15 | 13.501,00 | 0,2379 | 1.106.310 un. |
| **Red Propia** | Líquido Desinfectante | 27.119,90 | 7.257,99 | 7.446,54 | 0,2676 | 542.398 un. |
| **Red Propia** | Lavavajilla | 22.301,70 | 5.008,72 | 5.138,84 | 0,2246 | 446.034 un. |
| **Red Propia** | Líquido Lavar Ropa | 11.723,20 | 4.299,75 | 4.411,46 | 0,3668 | 234.464 un. |
| **Red Propia** | Suavizante | 8.887,20 | 2.412,51 | 2.475,19 | 0,2715 | 177.744 un. |
| **Red Propia** | Detergente Concentrado | 4.677,95 | 2.108,59 | 2.163,36 | 0,4507 | 93.559 un. |

---

## 4. Distribuciones Estocásticas y Sintaxis AnyLogic

Expresiones listas para copiar en los bloques de demanda (`Source`, `Uniform`, `Normal`, `Triangular`) en AnyLogic:

| Producto / Nivel | Media ($\mu$) | Desv. Muestral ($s$) | Distribución | Sintaxis AnyLogic Recomendada | Capacidad Asignada Sugerida (85% Util.) |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Demanda Global Planta** | 274.827 un. | 60.834 un. | Normal / Triangular | `normal(274827.0, 60834.1)` | **~316.000 un/mes** |
| **Lavandina** | 105.125 un. | 29.041 un. | Normal | `normal(105125.2, 29041.3)` | **~120.900 un/mes** |
| **Líquido Desinfectante** | 70.077 un. | 21.967 un. | Normal | `normal(70076.7, 21967.0)` | **~80.600 un/mes** |
| **Lavavajilla** | 51.042 un. | 15.415 un. | Normal | `normal(51042.1, 15414.9)` | **~58.700 un/mes** |
| **Líquido Lavar Ropa** | 21.708 un. | 9.296 un. | Normal | `normal(21708.0, 9296.4)` | **~25.000 un/mes** |
| **Suavizante** | 18.014 un. | 5.378 un. | Normal | `normal(18014.0, 5378.0)` | **~20.700 un/mes** |
| **Detergente Concentrado** | 8.861 un. | 4.521 un. | Normal | `normal(8860.9, 4521.2)` | **~10.200 un/mes** |

---

## 5. Variabilidad por Canal y Validación del Efecto Látigo

* **Red Propia (428 clientes agregados):** $CV = 0,238$ $\rightarrow$ La suma de múltiples clientes chicos/medianos estabiliza la demanda agregada hacia la fábrica.
* **Maxiconsumo (1 gran cliente mayorista):** $CV = 0,384$ $\rightarrow$ Pedidos periódicos en lotes mayores generan variabilidad media.
* **Grandes Clientes (Cadenas mayoristas: Makro, Treoland, Carrefour):** $CV = 0,494$ $\rightarrow$ Volatilidad alta y tasa de pérdida de venta / cancelación del 26,77% por quiebres de stock.

---

## 6. Archivos de Datos Relacionados

* [`demanda_mensual_anylogic_perfil_producto.csv`](file:///c:/Users/octab/Developer/Projects/SimulacionUTN/domitec/output/demanda_mensual_anylogic_perfil_producto.csv): Tabla de datos en CSV para importar a AnyLogic.
* [`resumen_productos_familias.csv`](file:///c:/Users/octab/Developer/Projects/SimulacionUTN/domitec/output/resumen_productos_familias.csv): Resumen de las 6 familias.
* [`resumen_canales_simplificado.csv`](file:///c:/Users/octab/Developer/Projects/SimulacionUTN/domitec/output/resumen_canales_simplificado.csv): Resumen por canal comercial.
