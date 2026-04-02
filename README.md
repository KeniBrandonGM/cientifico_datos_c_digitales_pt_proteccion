# Prueba Técnica — Científico de Datos para Soluciones con IA
**Equipo Canales Digitales · Protección**

Resultados de cada punto de la prueba tecnica usanod el dataset dado

---

## Estructura del proyecto

```
├── data/                        
│   ├── orders_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── customers_dataset.csv
│   ├── geolocation_dataset.csv
│   ├── products_dataset.csv
│   ├── sellers_dataset.csv
│   ├── order_payments_dataset.csv
│   ├── product_category_name_translation.csv
│   ├── clientes_segmentados.csv  # Generado por P3
│   └── malas_experiencias_clasificadas.csv  # Generado por P2
├── notebooks/
│   ├── 1_productos_mas_vendidos.ipynb
│   └── 2_dolores_malas_experiencias.ipynb
├── scripts/
│   ├── 2_dolores_malas_experiencias.py  # Clasificación NLP masiva con LLM
│   ├── 2b_cruce_productos.py
│   ├── 3_segmentacion_clientes.py
│   ├── 5_ubicacion_centro_comercial.py
├── outputs/
│   ├── p5_mapa_ubicacion.html      # Mapa interactivo São Paulo
│   ├── p6_base_conocimientos.json
└── docs/
    ├── p1_productos_mas_vendidos.md
    ├── p2_dolor_clientes.md
    ├── p3_segmentacion_clientes.md
    ├── p4_arquitectura_recomendador.md
    ├── p5_ubicacion_centro_comercial.md
    ├── p6_base_conocimientos.md
    └── p7_system_prompts.md
```

---

## Stack tecnológico

| Herramienta | Uso |
|---|---|
| Python 3.12 + uv | Entorno y gestión de dependencias |
| pandas, scikit-learn | Análisis de datos y clustering |
| LangChain + Ollama (`granite4:3b`) | Clasificación NLP Zero-Shot (P2) |
| folium | Mapas interactivos (P5) |
| seaborn / matplotlib | Visualizaciones |

---

## Resultados por pregunta

### P1 — Productos más vendidos
[`docs/p1_productos_mas_vendidos.md`](docs/p1_productos_mas_vendidos.md) · [`notebooks/1_productos_mas_vendidos.ipynb`](notebooks/1_productos_mas_vendidos.ipynb)

Análisis sobre 110.197 ítems entregados (órdenes `delivered`). Los ingresos se calculan como `price` sin `freight_value`.

| Ranking | Por volumen | Por ingresos |
|---|---|---|
| 1 | bed_bath_table — 10.953 uds | health_beauty — R$ 1.233.131 |
| 2 | health_beauty — 9.465 uds | watches_gifts — R$ 1.166.176 |
| 3 | sports_leisure — 8.431 uds | bed_bath_table — R$ 1.023.434 |
| 4 | furniture_decor — 8.160 uds | sports_leisure — R$ 954.852 |
| 5 | computers_accessories — 7.644 uds | computers_accessories — R$ 888.724 |

`watches_gifts` es #2 en ingresos sin aparecer en el top 5 de volumen — ticket promedio de R$ 199 frente a R$ 93 de `bed_bath_table`.

---

### P2 — Dolor del cliente y categorías problemáticas
[`docs/p2_dolor_clientes.md`](docs/p2_dolor_clientes.md) · [`notebooks/2_dolores_malas_experiencias.ipynb`](notebooks/2_dolores_malas_experiencias.ipynb)

Corpus analizado: **10.890 reseñas** de 1-2 estrellas con texto. Clasificación Zero-Shot con `granite4:3b` sobre una taxonomía de 6 categorías definida a partir de análisis de n-gramas del corpus.

| Categoría | Quejas | % |
|---|---|---|
| **Logistica_Retrasos** | 4.853 | 44.6% |
| Producto_Incorrecto_Faltante | 2.821 | 25.9% |
| Calidad_Producto | 1.958 | 18.0% |
| Reembolso_Atencion_Cliente | 473 | 4.3% |
| Otro / Fiscal | 785 | 7.2% |

El **70.5%** del malestar tiene origen en la cadena de entrega, no en el producto. Por tasa de insatisfacción normalizada (mín. 100 reseñas), `office_furniture` (21.2%) y `fashion_male_clothing` (23.7%) son las categorías más problemáticas.

---

### P3 — Segmentación de clientes
[`docs/p3_segmentacion_clientes.md`](docs/p3_segmentacion_clientes.md) · [`scripts/3_segmentacion_clientes.py`](scripts/3_segmentacion_clientes.py)

Framework RFM sobre 93.358 clientes únicos (`customer_unique_id`, solo órdenes `delivered`). K-Means puro no funcionó — el 97% de clientes tiene frequency=1, eliminando varianza en esa variable. Se adoptó un enfoque híbrido: regla de negocio (frequency ≥ 2) + K-Means sobre Recency y Monetary.

| Segmento | Clientes | % | Recency | Frecuencia | Gasto medio |
|---|---|---|---|---|---|
| Esporadico_Comun | 87.550 | 93.8% | 238 días | 1.0 | R$ 109 |
| Alto_Valor_Durmiente | 3.007 | 3.2% | 246 días | 1.0 | R$ 981 |
| Cliente_Fiel_En_Riesgo | 2.619 | 2.8% | 222 días | 2.1 | R$ 205 |
| Cliente_Fiel_Activo | 182 | 0.2% | 202 días | 2.5 | R$ 1.047 |

---

### P4 — Arquitectura: motor de recomendación en tiempo real
[`docs/p4_arquitectura_recomendador.md`](docs/p4_arquitectura_recomendador.md)

Diseño de arquitectura two-stage (candidate generation + ranking personalizado) con respuesta <100ms. Las recomendaciones se pre-computan en un pipeline offline y se sirven desde caché (Redis). El pipeline online solo orquesta lookups.

| Escenario | Algoritmo de ranking |
|---|---|
| Historial rico | Item-based Collaborative Filtering |
| Historial escaso (1 compra) | Content-Based Filtering |
| Cliente nuevo / anónimo | Top productos globales por segmento |

Stack propuesto: FastAPI · Redis · PostgreSQL · scikit-learn / implicit · Airflow.

---

### P5 — Ubicación óptima para el centro comercial
[`docs/p5_ubicacion_centro_comercial.md`](docs/p5_ubicacion_centro_comercial.md) · [`scripts/5_ubicacion_centro_comercial.py`](scripts/5_ubicacion_centro_comercial.py)

**Ciudad seleccionada: São Paulo (SP)** — R$ 1.859.556 en ingresos, 15.045 órdenes. Casi el doble que Río de Janeiro, segunda ciudad del ranking.

Punto óptimo calculado como **centroide ponderado por ingresos** sobre las coordenadas de 15.043 clientes:

```
Latitud:   -23.571436
Longitud:  -46.633771
Zona:      Perdizes / Pompeia, São Paulo
```

El 80% de los clientes de São Paulo se encuentra en un radio de **15.19 km** del punto. Mapas interactivos disponibles en `outputs/`.

---

### P6 — Base de conocimientos para el agente de IA
[`docs/p6_base_conocimientos.md`](docs/p6_base_conocimientos.md) · [`scripts/6_base_conocimientos.py`](scripts/6_base_conocimientos.py)

Base de conocimientos en JSON (`outputs/p6_base_conocimientos.json`) con 3 productos seleccionados del top de P1, precios reales del dataset y descripciones orientadas a un agente de ventas conversacional.

| Producto | Categoría | Precio promedio | Unidades vendidas |
|---|---|---|---|
| Kit de Belleza y Cuidado Personal Premium | health_beauty | R$ 130.28 | 9.465 |
| Colección Hogar: Cama, Baño y Mesa | bed_bath_table | R$ 93.44 | 10.953 |
| Relojes y Regalos Exclusivos | watches_gifts | R$ 199.04 | 5.859 |

---

### P7 — System Prompts para agente IA hiper-personalizado
[`docs/p7_system_prompts.md`](docs/p7_system_prompts.md) · [`scripts/7_system_prompts_agente.py`](scripts/7_system_prompts_agente.py)

Arquitectura `CustomerState → Middleware → System Prompt dinámico`, diseñada para modelos de producción (Claude, GPT-4o, Gemini). El middleware selecciona el prompt adecuado mediante reglas determinísticas y enriquece el contexto antes de invocar al LLM.

**3 personas diferenciadas:**

| Persona | Escenario | Tono |
|---|---|---|
| Luna | Joven (27F), Cliente_Fiel_Activo, perfil digital frecuente | Casual, tuteo, proactivo |
| Marco | Mayor (62M), Cliente_Fiel_En_Riesgo, mala experiencia previa | Formal, empático, sin presión |
| Asesor VIP | Corporativo (45M), Alto_Valor_Durmiente, mayor gasto del segmento | Premium, anticipatorio, concierge |

El contexto del cliente (perfil + catálogo) se pasa como JSON estructurado. Skill única: `check_order_status` (integración con API de órdenes externa). La recomendación de productos y el manejo de quejas se delegan al razonamiento del modelo.

Los prompts renderizados con datos reales del dataset están disponibles en `outputs/p7_diseno_agente.json`.

---

## Cómo ejecutar

**Requisito:** Python 3.12+ con [uv](https://docs.astral.sh/uv/) instalado.

```bash
# Instalar dependencias
uv sync

# P1 — Análisis productos más vendidos
# Abrir notebooks/1_productos_mas_vendidos.ipynb

# P2 — Clasificación NLP (requiere Ollama con granite4:3b corriendo)
uv run python scripts/2_dolores_malas_experiencias.py full

# P3 — Segmentación de clientes
uv run python scripts/3_segmentacion_clientes.py

# P5 — Ubicación centro comercial + mapas
uv run python scripts/5_ubicacion_centro_comercial.py

```

> P2 en modo `full` requiere Ollama corriendo localmente con el modelo `granite4:3b`. Usar `test` para validar con 10 comentarios.

---

## Supuestos globales del análisis

- **"Venta realizada"** = órdenes con `order_status == 'delivered'` en todos los análisis.
- **Ingresos** = `price` del ítem, sin incluir `freight_value` (costo logístico, no precio del producto).
- **Cliente único** = `customer_unique_id`
- **Variables CRM** (edad, género en P7) = simuladas por escenario, como indica el enunciado de la prueba.
