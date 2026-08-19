Se ha creado y ejecutado con éxito el script integral de análisis de demanda [`domitec_demand_analysis.py`](file:///c:/Users/octab/Developer/projects/SimulacionUTN/domitec/domitec_demand_analysis.py) dentro del entorno virtual `.venv`.

A partir de los **23.689 registros históricos** (enero 2025 a agosto 2026, 20 meses continuos) y un volumen total de **5.853.595 unidades demandadas**, se presentan los resultados clave estructurados para el diseño del modelo en **AnyLogic**.

---

### 📌 Resumen Ejecutivo de Métricas Globales

* **Volumen Total Demandado (Pedidos):** 5.853.595 unidades (promedio mensual: 292.680 un/mes).
* **Volumen Total Despachado:** 5.018.050 unidades.
* **Fill Rate Global (Nivel de Servicio):** **85,73%**.
* **Volumen Cancelado (Venta Perdida):** 589.511 unidades (**10,07%** de los pedidos).
* **Volumen Pendiente:** 246.034 unidades (**4,20%**).
* **Concentración HHI:** 1.269,4 (concentración moderada-alta en pocos mayoristas).

---

## 1. Clasificación y Segmentación de Clientes

Se analizaron los **437 clientes activos** bajo clasificación **ABC de Pareto**, métricas de regularidad (**RFM**), variabilidad de demanda ($CV = \sigma / \mu$) y tasa de cumplimiento (**Fill Rate**).

### A. Clasificación ABC de Clientes

| Clase ABC | Cantidad de Clientes | % de Clientes | % Volumen Demandado | Comportamiento Típico |
| :---: | :---: | :---: | :---: | :--- |
| **A** | **69** | 15,8% | **79,8%** | Cuentas clave y grandes distribuidores con compras recurrentes. |
| **B** | **146** | 33,4% | **15,2%** | Distribuidores regionales medianos con pedidos mensuales regulares. |
| **C** | **222** | 50,8% | **5,0%** | Minoristas y autoservicios chicos con pedidos intermitentes/esporádicos. |

### B. Top 10 Clientes y Asignación de Roles en AnyLogic

| # | Cliente | Canal (`VentasXnegocio`) | Pedidos Totales | Share Vol. | Share Acum. | Fill Rate | CV Demanda | Rol Arquitectónico Recomendado en AnyLogic |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | **MAXICONSUMO S.A.** | MAXICONSUMO | 1.997.646 | **34,13%** | 34,13% | 85,7% | 0,399 | **Agente Individual Clave** (*Key Account Agent*) |
| 2 | **SUPERM. MAYORISTAS MAKRO** | GRANDES CLIENTES | 459.053 | **7,84%** | 41,97% | 69,2% | 0,639 | **Agente Individual Clave** (*Key Account Agent*) |
| 3 | **TREOLAND SA** | GRANDES CLIENTES | 247.760 | **4,23%** | 46,20% | 67,4% | 0,968 | **Agente Individual Clave** (*Key Account Agent*) |
| 4 | **INC S. A. (Carrefour)** | GRANDES CLIENTES | 92.391 | **1,58%** | 47,78% | 74,8% | 1,110 | Población de Distribuidores Mayores |
| 5 | **GRUPO LEON SA** | RED PROPIA | 77.163 | **1,32%** | 49,10% | 81,3% | 0,446 | Población de Distribuidores Mayores |
| 6 | **EL CONDOR SRL** | RED PROPIA | 75.356 | **1,29%** | 50,39% | 89,7% | 0,498 | Población de Distribuidores Mayores |
| 7 | **BRUSA S.R.L.** | RED PROPIA | 72.676 | **1,24%** | 51,63% | 94,1% | 0,388 | Población de Distribuidores Mayores |
| 8 | **MARIANO IDELIO SANTOS S.R.L.** | RED PROPIA | 67.450 | **1,15%** | 52,78% | 88,4% | 0,800 | Población de Distribuidores Mayores |
| 9 | **SCHAFFER ALFREDO** | RED PROPIA | 67.310 | **1,15%** | 53,93% | 90,5% | 0,679 | Población de Distribuidores Mayores |
| 10 | **DEL SUR SRL** | RED PROPIA | 60.544 | **1,03%** | 54,96% | 92,2% | 0,676 | Población de Distribuidores Mayores |

> **Observación Clave para AnyLogic:**
>
> * **Top 1:** Solo Maxiconsumo representa más de **1/3 de toda la demanda** de la fábrica.
> * **Top 5:** Concentran el **49,1%** de los pedidos.
> * **Fill Rate bajo en Grandes Cuentas:** Makro (69,2%) y Treoland (67,4%) sufrieron las mayores tasas de cancelación/pérdida de venta por quiebre de stock en planta.

---

## 2. Agrupación y Clasificación de Productos

El catálogo activo cuenta con **10 Rubros (Familias)** y **29 SKUs específicos** (combinación Rubro + Presentación).

### A. Agrupación por Familias de Productos (Rubros)

| # | Rubro / Familia | Pedidos Totales | Share Vol. | Share Acum. | Fill Rate | Cancelación | CV Demanda |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **LAVANDINA COMUN** | 1.362.066 | **23,27%** | 23,27% | 91,7% | 4,89% | 0,248 |
| 2 | **LIQUIDO DESINFECTANTE** | 1.249.393 | **21,34%** | 44,61% | 82,1% | 14,55% | 0,334 |
| 3 | **LAVAVAJILLA** | 1.020.841 | **17,44%** | 62,05% | 87,3% | 7,57% | 0,302 |
| 4 | **LAVANDINA CONCENTRADA** | 740.438 | **12,65%** | 74,70% | 87,0% | 8,60% | 0,390 |
| 5 | **LIQUIDO LAVAR ROPA** | 434.161 | **7,42%** | 82,12% | 81,3% | 11,34% | 0,428 |
| 6 | **SUAVIZANTE** | 360.281 | **6,15%** | 88,27% | 79,5% | 14,56% | 0,299 |
| 7 | **PROMOPACK** | 355.656 | **6,08%** | 94,35% | 86,9% | 11,53% | 0,311 |
| 8 | **DETERGENTE CONCENTRADO** | 177.218 | **3,03%** | 97,38% | 86,8% | 6,91% | 0,510 |
| 9 | **LIQUIDO LIMPIADOR** | 152.141 | **2,60%** | 99,98% | 68,7% | 29,61% | 0,606 |
| 10 | **LIQUIDO BACTERICIDA** | 1.400 | **0,02%** | 100,00% | 90,4% | 9,64% | 3,078 |

### B. Matriz ABC - XYZ de SKUs (Volumen vs. Variabilidad)

* **X ($CV < 0.25$):** Demanda muy estable, ideal para Make-to-Stock (MTS) continuo.
* **Y ($0.25 \le CV < 0.50$):** Demanda con variabilidad moderada / estacional.
* **Z ($CV \ge 0.50$):** Demanda errática / compras en bultos esporádicos.

| Matriz | Cant. SKUs | Share Vol. | Fill Rate Prom. | Estrategia de Simulación / Producción |
| :---: | :---: | :---: | :---: | :--- |
| **AX** | 1 | **15,8%** | 92,9% | Producto insignia base: Stock de seguridad bajo, flujo continuo. |
| **AY** | 8 | **60,9%** | 86,0% | Núcleo de facturación: Requiere pronóstico suavizado y buffer dinámico. |
| **BX / BY** | 7 | **15,6%** | 82,1% | Rotación media: Reposición periódica $(s, S)$ en AnyLogic. |
| **BZ / CZ** | 12 | **7,3%** | 71,3% | Colas de catálogo: Make-to-Order (MTO) o lotes bajo pedido mínimo. |

### C. Top 6 SKUs y Selección de los 2-3 Productos para AnyLogic

| SKU (Producto + Presentación) | Total Pedidos | Share | Matriz | CV | Recomendación para el Modelo AnyLogic |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`LAVANDINA COMUN - 12X1 LT`** | 925.810 | **15,82%** | **AX** | **0,242** | **Producto 1 (Imprescindible):** Alta rotación, máxima estabilidad ($CV=0.24$), producto insignia. |
| **`LAVAVAJILLA - 15X750 CC`** | 896.685 | **15,32%** | **AY** | **0,329** | **Producto 2 (Opción A):** Alta rotación con estacionalidad moderada. |
| **`LIQUIDO DESINFECTANTE - 15X900 CC`** | 867.751 | **14,82%** | **AY** | **0,373** | **Producto 2 (Opción B):** Alta rotación, sensible a picos de demanda y quiebres. |
| **`LAVANDINA CONCENTRADA - 12X1 LT`** | 396.622 | **6,78%** | **AY** | **0,482** | **Producto 3 (Contraste):** Rotación media-alta con variabilidad cercana a Z ($CV=0.48$). |
| **`LIQUIDO DESINFECTANTE - 3X4.5 LT`** | 246.295 | **4,21%** | **AY** | **0,369** | **Alternativa Bidón:** Formato mayorista / institucional. |

---

## 3. Otras Métricas Clave y Parámetros para AnyLogic

### A. Validación Empírica del Efecto Látigo por Canal

Al comparar la variabilidad mensual ($CV$) de la demanda agregada según el tipo de cliente se observa el fenómeno descripto en el [`context.md`](file:///c:/Users/octab/Developer/projects/SimulacionUTN/domitec/context.md):

* **Red Propia (431 clientes medianos/chicos agrupados):** **$CV = 0,241$** *(Efecto agregación de demanda suaviza la varianza total)*.
* **Maxiconsumo (1 gran distribuidor nacional):** **$CV = 0,399$**.
* **Grandes Clientes (Makro, Treoland, Carrefour en pedidos en bloque):** **$CV = 0,655$** *(Máxima volatilidad y distorsión hacia la fábrica)*.

### B. Ajuste de Distribuciones Estocásticas para AnyLogic

Parámetros directos para programar los bloques de generación estocástica de pedidos en AnyLogic:

| Entidad / Producto | Nivel | Media ($\mu$) | Desv. ($\sigma$) | Distribución Ajustada | Sintaxis Lista para AnyLogic |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Demanda Total Fábrica** | Mensual Global | 292.680 un. | 64.472 un. | Normal / Triangular | `normal(292679.8, 64472.1)` o `triangular(162976, 298330, 420686)` |
| **`LAVANDINA COMUN - 12X1 LT`** | Mensual SKU | 46.291 un. | 11.203 un. | Normal | `normal(46290.5, 11203.2)` |
| **`LAVAVAJILLA - 15X750 CC`** | Mensual SKU | 44.834 un. | 14.767 un. | Normal / Triangular | `normal(44834.2, 14766.9)` |
| **`LIQ. DESINFECTANTE - 15X900 CC`** | Mensual SKU | 43.388 un. | 16.187 un. | Triangular | `triangular(10829, 43584, 72910)` |
| **`LAVANDINA CONC. - 12X1 LT`** | Mensual SKU | 19.831 un. | 9.567 un. | Triangular / Lognormal | `triangular(6591, 18867, 44510)` |

### C. Capacidad Efectiva de Producción y Buffers Sugeridos

Para evitar subdimensionar o sobredimensionar la planta `DomitecPlant`:

* **Capacidad promedio sugerida (factor de utilización 85%):**
  * Demanda global: **~336.500 unidades/mes**.
  * Línea Lavandina 1L: **~53.200 unidades/mes**.
  * Línea Lavavajilla 750cc: **~51.500 unidades/mes**.
  * Línea Desinfectante 900cc: **~49.900 unidades/mes**.
* **Stock de Seguridad Sugerido ($z=1.65$ para 95% de nivel de servicio):**
  * Para $L = 2$ semanas: $SS = 1.65 \times \sigma_{\text{semanal}} \approx 9.200$ un. para Lavandina 1L.
