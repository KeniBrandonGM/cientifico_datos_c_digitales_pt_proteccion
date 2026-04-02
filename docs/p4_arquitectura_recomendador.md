# P4 — Arquitectura: Motor de Recomendación en Tiempo Real

## Objetivo

Recomendar automáticamente productos relevantes cuando un cliente visita la web, combinando su **perfil de segmento** (obtenido en P3) con su **historial de compras** y **comportamiento de navegación**, con respuesta en tiempo real (<100ms).

---

## Principio de diseño central

El modelo **no se ejecuta en tiempo real**. Las recomendaciones se pre-computan en un pipeline offline y se sirven como simples lecturas de caché. El pipeline online solo orquesta lookups y aplica personalización ligera.

---

## Arquitectura en dos etapas (Two-Stage Recommender)

### Etapa 1 — Candidate Generation (filtro por perfil de segmento)

- Se toma el `cluster_id` del cliente (asignado en P3).
- Se recupera el pool de productos más relevantes para ese segmento: productos más comprados, mejor valorados y con mayor ingreso dentro del cluster.
- Resultado: **50–200 productos candidatos**, pre-computados y almacenados en caché.
- Excluye automáticamente productos que el cliente ya compró.

**Propósito:** reducir el espacio de búsqueda antes de aplicar el algoritmo de ranking, mejorando velocidad y precisión.

### Etapa 2 — Ranking (personalización por historial individual)

Sobre el pool de candidatos se aplica un algoritmo de recomendación según la riqueza del historial:

| Escenario | Algoritmo | Razón |
|---|---|---|
| Cliente con varios productos comprados | **Item-based Collaborative Filtering** | Encuentra ítems similares a los ya comprados usando co-ocurrencia; robusto ante matrices dispersas |
| Cliente con 1 o muy pocas compras | **Content-Based Filtering** | Usa features del producto (categoría, precio, características) para encontrar similares sin necesitar historial denso |
| Cliente nuevo / anónimo (cold start) | Top productos globales o por categoría | Sin perfil ni historial, se sirven los más populares |

---

## Señales de entrada al sistema

### Señales explícitas
- Historial de compras (`order_items` → `product_id`)
- Score de reseñas del cliente

### Señales implícitas (comportamiento de navegación)
- Productos vistos y no comprados (tracking via cookies/sesión)
- Clicks en productos
- Tiempo de permanencia en una página de producto
- Productos añadidos al carrito sin comprar

Estas señales se usan como **interacciones de menor peso** que una compra real en el modelo de ranking. Con un dataset de alta esparsidad, el comportamiento implícito es especialmente valioso porque multiplica el volumen de señal disponible por usuario.

---

## Flujo completo

```
Cliente visita la web
        │
        ▼
¿Tenemos customer_id?
   │                   │
  SÍ                   NO → Cold start: top productos globales
   │
   ▼
Lookup en base de datos:
  · cluster_id (perfil de segmento)
  · historial de compras (product_ids)
  · comportamiento implícito (vistas, clicks)
        │
        ▼
ETAPA 1 — Candidate Generation
  · Leer pool pre-computado del cluster desde Redis
  · Filtrar productos ya comprados
        │
        ▼
ETAPA 2 — Ranking personalizado
  · ¿Historial rico?  → Item-based CF
  · ¿Historial pobre? → Content-Based Filtering
  · Incorporar señales implícitas como peso adicional
        │
        ▼
Devolver top-N productos al frontend
```

---

## Pipeline offline (batch)

Se ejecuta periódicamente (ej. cada 24 horas o tras un volumen significativo de nuevas compras):

1. **Actualizar perfiles de segmento:** re-asignar `cluster_id` a clientes con actividad reciente.
2. **Recomputar pools por cluster:** recalcular top productos por segmento con datos frescos.
3. **Actualizar matrices de similaridad:** recalcular co-ocurrencias y features para Item-based CF y Content-Based.
4. **Publicar en caché (Redis):** reemplazar los valores anteriores de forma atómica.

---

## Feedback Loop

Componente crítico para que el sistema mejore con el tiempo:

- Se registra cada recomendación servida: `(customer_id, product_id, timestamp, posición)`.
- Se registra la acción posterior del cliente: compra, click, ignorado.
- Métricas de evaluación continua: **CTR** (click-through rate), **conversion rate**, **coverage**.
- Los datos de feedback alimentan el pipeline offline en el siguiente ciclo de reentrenamiento.

Sin el feedback loop, el sistema es estático y no aprende del comportamiento real de los usuarios.

---

## Stack tecnológico

| Componente | Tecnología | Rol |
|---|---|---|
| API de recomendaciones | **FastAPI** | Endpoint REST, orquesta el flujo online |
| Caché de candidatos | **Redis** | Pools por cluster, lecturas <5ms |
| Base de datos de perfiles | **PostgreSQL** | cluster_id, historial, comportamiento implícito |
| Algoritmos de ranking | **Python (scikit-learn / implicit)** | Item-based CF y Content-Based |
| Pipeline offline | **Python + cron / Airflow** | Reentrenamiento y actualización del caché |
| Tracking implícito | **Eventos frontend → endpoint ligero** | Captura de vistas, clicks, carrito |

---

## Supuestos asumidos

1. El sistema de autenticación web provee el `customer_id` en la sesión (o cookie persistente).
2. Los datos de comportamiento implícito (vistas, clicks) provienen de un sistema de tracking frontend ya existente o implementado en paralelo.
3. El pipeline offline corre con la frecuencia adecuada al volumen de nuevas transacciones del negocio.
4. Para la demo/prueba técnica, el modelo se evalúa sobre el dataset histórico; en producción se alimentaría de datos en streaming.
