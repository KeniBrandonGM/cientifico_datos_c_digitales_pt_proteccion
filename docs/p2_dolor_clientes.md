# P2 — Dolor del Cliente y Categorías Problemáticas

## Pregunta
> ¿Cuál es el mayor dolor de nuestros clientes y qué productos o categorías están directamente relacionados con estas malas experiencias?

---

## Metodología

### Corpus analizado
- **Fuente:** `order_reviews_dataset` (99.224 reseñas totales)
- **Filtro aplicado:** `review_score` de 1 o 2 estrellas **con** comentario de texto no nulo
- **Corpus final:** 10.890 comentarios negativos con texto

### Clasificación NLP (Zero-Shot)
Cada comentario fue clasificado con el modelo LLM local **granite4:3b** (via Ollama + LangChain) dentro de una taxonomía fija de 6 categorías, forzando salida estructurada:

| Categoría | Descripción |
|---|---|
| `Logistica_Retrasos` | Producto no recibido, llegó tarde, problemas con el transportista |
| `Producto_Incorrecto_Faltante` | Ítem equivocado, faltante o diferente al pedido |
| `Calidad_Producto` | Defectuoso, roto, de mala calidad o diferente a la foto |
| `Reembolso_Atencion_Cliente` | Solicitud de devolución, sin respuesta, mal servicio |
| `Problema_Fiscal_Burocracia` | Problemas con nota fiscal, facturación o documentos |
| `Otro` | Lo que no encaja en las categorías anteriores |

La taxonomía fue definida a partir de un **análisis previo de frecuencia de n-gramas** sobre el corpus, garantizando que refleje los temas reales del dataset y no supuestos externos.

---

## Resultado 1 — Distribución del dolor del cliente

| Categoría | Quejas | % del total |
|---|---|---|
| **Logistica_Retrasos** | **4.853** | **44.6%** |
| Producto_Incorrecto_Faltante | 2.821 | 25.9% |
| Calidad_Producto | 1.958 | 18.0% |
| Otro | 652 | 6.0% |
| Reembolso_Atencion_Cliente | 473 | 4.3% |
| Problema_Fiscal_Burocracia | 133 | 1.2% |

**El mayor dolor identificado es la logística.** Casi 1 de cada 2 clientes insatisfechos se queja de no haber recibido su producto o de retrasos en la entrega. Sumando `Logistica_Retrasos` y `Producto_Incorrecto_Faltante`, el **70.5% del malestar tiene origen en la cadena de entrega**, no en el producto en sí.

---

## Resultado 2 — ¿Qué categorías están relacionadas con las malas experiencias?

Para responder esta pregunta se aplicaron **dos enfoques complementarios**, ya que cada uno revela una dimensión diferente del problema.

---

### Enfoque A — Volumen absoluto de quejas por categoría

Cuenta el número bruto de reseñas negativas por categoría de producto.

**Supuesto:** útil para saber dónde se concentra el mayor volumen de clientes insatisfechos y dónde el equipo de soporte recibe más presión operativa.

| Categoría | Quejas negativas | Total reseñas de la categoría | % de sus reseñas |
|---|---|---|---|
| bed_bath_table | 1.623 | 11.137 | 14.6% |
| furniture_decor | 1.215 | 8.331 | 14.6% |
| computers_accessories | 1.140 | 7.849 | 14.5% |
| health_beauty | 998 | — | — |
| sports_leisure | 985 | — | — |
| housewares | 859 | — | — |
| watches_gifts | 742 | 5.950 | 12.5% |
| telephony | 583 | 4.517 | 12.9% |

> **Advertencia de interpretación:** estas categorías encabezan el ranking principalmente porque son las más vendidas (ver P1). Tener más ventas implica naturalmente más reseñas negativas en términos absolutos. Este enfoque no mide si una categoría es *más propensa* a generar insatisfacción.

---

### Enfoque B — Tasa de insatisfacción por categoría *(enfoque correcto)*

Calcula el porcentaje de reseñas negativas sobre el **total de reseñas** de cada categoría.

**Supuesto analítico:** solo se consideran categorías con un mínimo de **100 reseñas** para garantizar significancia estadística (53 de 74 categorías cumplen el umbral).

> **Fórmula:** `Tasa = (reseñas negativas de la categoría / total de reseñas de la categoría) × 100`

| Categoría | Total reseñas | Quejas negativas | Tasa de insatisfacción |
|---|---|---|---|
| **fashion_male_clothing** | 131 | 31 | **23.7%** |
| **office_furniture** | 1.687 | 357 | **21.2%** |
| **fixed_telephony** | 262 | 51 | **19.5%** |
| unknown_category | 1.598 | 273 | 17.1% |
| home_confort | 435 | 74 | 17.0% |
| construction_tools_safety | 193 | 31 | 16.1% |
| audio | 361 | 56 | 15.5% |
| air_conditioning | 292 | 44 | 15.1% |
| furniture_decor | 8.331 | 1.215 | 14.6% |
| bed_bath_table | 11.137 | 1.623 | 14.6% |

> **`bed_bath_table`**, que lideraba el enfoque A, cae al puesto 10 con una tasa del 14.6% — vende mucho, pero no es desproporcionadamente problemática. El **verdadero problema** está en categorías como `office_furniture` (1 de cada 5 clientes insatisfecho) y `fashion_male_clothing` (casi 1 de cada 4).

---

### Tasa de insatisfacción por tipo de dolor

**Logistica_Retrasos** — categorías con mayor tasa de retrasos/no entrega:

| Categoría | Total reseñas | Quejas logística | Tasa |
|---|---|---|---|
| fashion_male_clothing | 131 | 12 | 9.2% |
| fashion_underwear_beach | 130 | 12 | 9.2% |
| fixed_telephony | 262 | 23 | 8.8% |
| office_furniture | 1.687 | 127 | 7.5% |
| furniture_living_room | 502 | 37 | 7.4% |

**Producto_Incorrecto_Faltante** — categorías con mayor tasa de errores en el pedido:

| Categoría | Total reseñas | Quejas producto incorrecto | Tasa |
|---|---|---|---|
| fashion_male_clothing | 131 | 12 | 9.2% |
| office_furniture | 1.687 | 141 | 8.4% |
| costruction_tools_garden | 240 | 20 | 8.3% |
| fixed_telephony | 262 | 19 | 7.3% |
| signaling_and_security | 197 | 14 | 7.1% |

**Calidad_Producto** — categorías con mayor tasa de defectos/calidad:

| Categoría | Total reseñas | Quejas calidad | Tasa |
|---|---|---|---|
| audio | 361 | 19 | 5.3% |
| art | 207 | 9 | 4.3% |
| office_furniture | 1.687 | 62 | 3.7% |
| home_confort | 435 | 15 | 3.4% |

---

## Conclusión ejecutiva

**El mayor dolor del cliente es la logística** — el 70.5% de las quejas apuntan a problemas de entrega (retrasos, productos no recibidos o incorrectos). Este problema es **transversal a todo el catálogo**, no exclusivo de una categoría.

Sin embargo, al normalizar por tasa de insatisfacción, emergen las categorías realmente problemáticas:

- **`office_furniture`** es la categoría de alto volumen más crítica: 21.2% de tasa y aparece en el top de *tres* tipos de dolor (logística, producto incorrecto y calidad). Requiere atención prioritaria.
- **`fashion_male_clothing`** y **`fixed_telephony`** tienen las tasas más altas del dataset, aunque con menor volumen absoluto.
- Las categorías estrella de ventas (`bed_bath_table`, `health_beauty`) tienen tasas moderadas (~14%) — su alto volumen de quejas absolutas es proporcional a sus ventas.

### Recomendación de negocio
La solución no pasa por gestionar categorías individualmente, sino por **fortalecer la cadena logística de forma sistémica**. Las categorías con alta tasa como `office_furniture` merecen una revisión adicional de sus proveedores y procesos de picking/packing, dado que acumulan múltiples tipos de dolor simultáneamente.

---

## Supuestos asumidos

1. Se consideran "malas experiencias" únicamente las reseñas con `review_score` de 1 o 2 estrellas que contienen texto (`review_comment_message` no nulo). Las reseñas sin texto quedan fuera del análisis NLP.
2. El umbral mínimo de 100 reseñas por categoría para el cálculo de tasa es una convención estadística para evitar que categorías con muy pocas reseñas distorsionen el ranking.
3. La clasificación es Zero-Shot (sin fine-tuning sobre este dominio). Se asume que el modelo `granite4:3b` captura correctamente los patrones del portugués brasileño con el prompt diseñado, validado sobre una muestra de 10 comentarios.
