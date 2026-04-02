# Pregunta 1 — Top 5 Productos Más Vendidos por Volumen e Ingresos

## Objetivo

Identificar las 5 categorías de productos más vendidas en términos de **volumen de unidades** y las 5 con mayor **ingreso total**, a partir del dataset.

---

## Datasets utilizados

| Dataset | Registros | Rol |
|---|---|---|
| `orders_dataset.csv` | 99.441 | Estado de cada pedido |
| `order_items_dataset.csv` | 112.650 | Items por pedido, precio y vendedor |
| `products_dataset.csv` | 32.951 | Categoría de cada producto |
| `product_category_name_translation.csv` | 71 | Traducción categorías PT → EN |

---

## Desarrollo

### 1. Filtro por estado `delivered`

El dataset de órdenes incluye pedidos en múltiples estados:

| Estado | Cantidad |
|---|---|
| delivered | 96.478 |
| shipped | 1.107 |
| canceled | 625 |
| unavailable | 609 |
| invoiced | 314 |
| processing | 301 |
| created / approved | 7 |

**Supuesto:** Solo se consideran órdenes con estado `delivered` como "producto vendido". Bajo una perspectiva financiera, únicamente los pedidos efectivamente entregados representan ingresos realizados. Los pedidos cancelados, en tránsito o con incidencias no se contabilizan.

### 2. Construcción del dataframe analítico

Se realizaron 3 joins secuenciales:

```
orders_dataset (delivered)
    → inner join order_items_dataset  (on: order_id)   → precio y product_id
    → inner join products_dataset     (on: product_id) → categoría en portugués
    → left join  translation          (on: category)   → categoría en inglés
```

El resultado fue un dataframe de **110.197 filas × 23 columnas**, donde cada fila representa un ítem vendido y entregado con su categoría y precio.

### 3. Manejo de nulos en categorías

El join con `products_dataset` dejó 1.537 productos sin categoría (productos sin metadatos en el catálogo). El join de traducción añadió 22 filas adicionales sin traducción disponible.

**Estrategia:** se creó la columna `categoria_producto_final` con la siguiente jerarquía de fallback:

```python
categoria_producto_final = product_category_name_english
                        ?? product_category_name   # si no hay traducción
                        ?? 'unknown_category'       # si tampoco hay nombre PT
```

Esto preserva el 100% de las filas en el análisis, asignando los productos sin categoría a `unknown_category` (~1,4% del total).

### 4. Métrica de ingresos

Los ingresos se calcularon usando la columna `price` del dataset de items.  
**No se incluye `freight_value`**: el flete es un costo logístico, no el precio del producto en sí. Esta distinción es relevante para análisis de rentabilidad por categoría.

---

## Resultados

### Top 5 por Volumen (unidades vendidas)

| # | Categoría | Unidades vendidas |
|---|---|---|
| 1 | bed_bath_table | 10.953 |
| 2 | health_beauty | 9.465 |
| 3 | sports_leisure | 8.431 |
| 4 | furniture_decor | 8.160 |
| 5 | computers_accessories | 7.644 |

### Top 5 por Ingresos totales (R$)

| # | Categoría | Ingresos totales |
|---|---|---|
| 1 | health_beauty | R$ 1.233.131,72 |
| 2 | watches_gifts | R$ 1.166.176,98 |
| 3 | bed_bath_table | R$ 1.023.434,76 |
| 4 | sports_leisure | R$ 954.852,55 |
| 5 | computers_accessories | R$ 888.724,61 |

---

## Insights

- **Los rankings no coinciden:** `watches_gifts` es el #2 en ingresos pero no aparece en el top 5 de volumen. Esto indica un **ticket promedio alto** (R$199 promedio vs. R$93 de bed_bath_table), posicionándolo como categoría premium de bajo volumen pero alta rentabilidad.

- **`furniture_decor`** es el #4 en volumen pero no entra al top 5 en ingresos, lo que sugiere un precio unitario bajo y márgenes ajustados.

- **`health_beauty`** es la única categoría presente como #1 en ingresos y #2 en volumen, confirmándola como la **categoría estrella** del catálogo: masiva en demanda y rentable al mismo tiempo.

- **`bed_bath_table`** lidera en volumen (#1) pero cae al #3 en ingresos, indicando alta rotación con ticket promedio moderado (R$93).

---

## Archivos

| Archivo | Descripción |
|---|---|
| `notebooks/1_productos_mas_vendidos.ipynb` | Análisis completo con código y outputs |
