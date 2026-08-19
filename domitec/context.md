chat en mi materia de simulacion vamos a realizar el siguiente trabajo relacionado con este paper que adjunto.

# Contexto del TP: Simulación del Efecto Látigo en Domitec S.A

## Objetivo del trabajo

Grupo de trabajo va a construir una simulación en **AnyLogic** del efecto látigo (bullwhip effect) en la cadena de suministro de **Domitec S.A.**, empresa fabricante de productos de limpieza/desinfección (lavandina, detergente, jabón líquido, suavizante, desinfectantes). El proyecto se basa en el paper *"Analysis of Bullwhip Effect Based on ABMS"* (Wu, Gan, Wei — Procedia Engineering, 2011), que modela una cadena de 5 eslabones con agentes que pronostican demanda (suavizado exponencial) y ajustan pedidos según inventario actual vs. objetivo, generando amplificación de la variabilidad hacia arriba en la cadena.

El acceso a datos reales lo brinda un familiar de uno de los integrantes, que es **gerente de producción en Domitec**.

## Modelo de cadena adoptado

```
Proveedores (materias primas/envases) → Domitec (planta) → Distribuidores/mayoristas → Puntos de venta (supermercados, cadenas) → Consumidor final
```

## Diseño de agentes en AnyLogic (definido hasta ahora)

- **`Supplier`**: agente simple, entrega insumos con delay tras recibir pedido de la planta.
- **`DomitecPlant`**: agente central (equivalente al "manufacturer" del paper + etapa de producción real). Statechart tipo `Esperando pedidos → Evaluando producción → Produciendo → Despachando`. Internamente maneja un `ProductState` por producto (inventario, pedido pendiente, pronóstico, capacidad efectiva) en vez de duplicar agentes por producto — permite escalar a varias líneas sin explotar la cantidad de agentes.
- **`Distributor`**: población de agentes, misma lógica de pronóstico/reposición que el "wholesaler" del paper.
- **`PointOfSale`**: población de agentes (supermercados/cadenas), equivalente al "retailer".
- **`Consumer`**: generador de demanda estocástica, sin lógica de decisión compleja.
- Interacción entre agentes vía mensajería con delay (equivalente a orderRequest/orderReceive/sendProduct/receiveProduct del paper), no function calls directas.

**Puntos abiertos de diseño de AnyLogic:**

- Cómo evitar que la capacidad de planta quede sobredimensionada al modelar solo 2-3 productos de un catálogo mucho más grande. Se evaluaron: (a) capacidad efectiva por producto como parámetro fijo (opción elegida para la primera versión), o (b) `ResourcePool` compartido con contención real entre productos modelados (para una segunda iteración).
- Statechart detallado de `DomitecPlant` — pendiente de definir en profundidad.

## Recolección de datos (en curso, previa a la implementación)

Se armó una planilla Excel con 6 hojas para que el gerente de producción complete, con fila de ejemplo por hoja:

1. Demanda y Pedidos
2. Producción (capacidad, lead time, tamaño de lote)
3. Inventario (stock actual/objetivo, costos)
4. Lead Times de la Cadena (proveedor→planta→distribuidor→PDV)
5. Política y Pronóstico (cómo deciden hoy cuánto producir/pedir, promociones, estacionalidad)
6. Estructura de la Cadena (panorama general, no por producto)

**Decisiones clave sobre cómo pedir los datos:**

- **Capacidad de producción**: pedir la capacidad *efectiva ya asignada* a cada producto específico (horas/semana dedicadas × ritmo de producción), no la capacidad teórica total de la planta — para que el modelo no muestre holgura irreal.
- **Demanda por segmento de cliente**: separar en niveles (distribuidores/cadenas grandes de forma individual, vs. "clientes chicos" agregados en un solo canal). Para el segmento agregado, el dato pedido es la **suma total** de pedidos por período (no el promedio por cliente) — esto además captura correctamente que la demanda agregada de muchos clientes chicos independientes tiende a suavizarse (menor variabilidad relativa) comparada con un distribuidor grande que pide en bloques, lo cual es relevante para mostrar el contraste del efecto látigo entre segmentos.

## Alcance

Empezar con 2-3 productos representativos (ej. uno de alta rotación y uno de menor rotación) antes de escalar al resto del catálogo.
