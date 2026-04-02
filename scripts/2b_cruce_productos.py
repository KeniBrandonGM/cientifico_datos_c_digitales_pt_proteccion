import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

MIN_REVIEWS = 100  # volumen mínimo para significancia estadística

# --- Carga ---
clasificadas  = pd.read_csv(DATA_DIR / 'malas_experiencias_clasificadas.csv')
order_reviews = pd.read_csv(DATA_DIR / 'order_reviews_dataset.csv')
order_items   = pd.read_csv(DATA_DIR / 'order_items_dataset.csv')
products      = pd.read_csv(DATA_DIR / 'products_dataset.csv')
translation   = pd.read_csv(DATA_DIR / 'product_category_name_translation.csv')

# Helper: añadir categoría final a un dataframe que ya tiene product_id
def add_categoria(df):
    df = df.merge(products[['product_id', 'product_category_name']], on='product_id', how='left')
    df = df.merge(translation, on='product_category_name', how='left')
    df['categoria'] = (
        df['product_category_name_english']
        .fillna(df['product_category_name'])
        .fillna('unknown_category')
    )
    return df

# =============================================================================
# DENOMINADOR: total de reseñas por categoría (todas las estrellas)
# =============================================================================
todas = order_reviews.merge(order_items[['order_id', 'product_id']], on='order_id', how='inner')
todas = add_categoria(todas)

total_por_categoria = (
    todas.groupby('categoria')['review_id']
    .count()
    .reset_index(name='total_resenas')
)

# =============================================================================
# NUMERADOR: reseñas negativas (1-2 estrellas) por categoría
# =============================================================================
malas = clasificadas.merge(order_items[['order_id', 'product_id']], on='order_id', how='inner')
malas = add_categoria(malas)

malas_por_categoria = (
    malas.groupby('categoria')['review_id']
    .count()
    .reset_index(name='resenas_negativas')
)

# =============================================================================
# TASA DE INSATISFACCIÓN
# =============================================================================
tasa = total_por_categoria.merge(malas_por_categoria, on='categoria', how='left')
tasa['resenas_negativas'] = tasa['resenas_negativas'].fillna(0).astype(int)
tasa['tasa_insatisfaccion'] = (tasa['resenas_negativas'] / tasa['total_resenas'] * 100).round(1)

# Filtro de significancia estadística
tasa_filtrada = tasa[tasa['total_resenas'] >= MIN_REVIEWS].copy()
tasa_filtrada = tasa_filtrada.sort_values('tasa_insatisfaccion', ascending=False)

print("="*70)
print(f"TASA DE INSATISFACCIÓN POR CATEGORÍA (min. {MIN_REVIEWS} reseñas)")
print("="*70)
print(f"\nCategorías con datos suficientes: {len(tasa_filtrada)} de {len(tasa)} totales")
print(f"\n{'Categoría':<35} {'Total':>8} {'Negativas':>10} {'Tasa %':>8}")
print("-"*65)
for _, row in tasa_filtrada.head(20).iterrows():
    print(f"{row['categoria']:<35} {row['total_resenas']:>8} {row['resenas_negativas']:>10} {row['tasa_insatisfaccion']:>7.1f}%")

# =============================================================================
# TASA POR TIPO DE DOLOR — top 5 categorías más problemáticas por pain point
# =============================================================================
print("\n" + "="*70)
print("TOP 5 CATEGORÍAS CON MAYOR TASA DE INSATISFACCIÓN POR TIPO DE DOLOR")
print("="*70)

pain_order = [
    'Logistica_Retrasos',
    'Producto_Incorrecto_Faltante',
    'Calidad_Producto',
    'Reembolso_Atencion_Cliente',
    'Problema_Fiscal_Burocracia',
]

for pain in pain_order:
    malas_pain = (
        malas[malas['pain_point_category'] == pain]
        .groupby('categoria')['review_id']
        .count()
        .reset_index(name='resenas_negativas_pain')
    )
    tasa_pain = tasa_filtrada[['categoria', 'total_resenas']].merge(malas_pain, on='categoria', how='inner')
    tasa_pain['tasa'] = (tasa_pain['resenas_negativas_pain'] / tasa_pain['total_resenas'] * 100).round(1)
    tasa_pain = tasa_pain.sort_values('tasa', ascending=False).head(5)

    print(f"\n[{pain}]")
    print(f"  {'Categoría':<35} {'Total':>7} {'Pain quejas':>12} {'Tasa %':>8}")
    print(f"  {'-'*65}")
    for _, row in tasa_pain.iterrows():
        print(f"  {row['categoria']:<35} {row['total_resenas']:>7} {row['resenas_negativas_pain']:>12} {row['tasa']:>7.1f}%")

# =============================================================================
# RESUMEN EJECUTIVO
# =============================================================================
print("\n" + "="*70)
print("RESUMEN EJECUTIVO")
print("="*70)

top3 = tasa_filtrada.head(3)
print(f"\nCategorías con MAYOR tasa de insatisfacción (con volumen significativo):")
for _, row in top3.iterrows():
    print(f"  · {row['categoria']}: {row['tasa_insatisfaccion']}% ({row['resenas_negativas']} negativas de {row['total_resenas']} reseñas)")

dist = clasificadas['pain_point_category'].value_counts()
pct_log = dist['Logistica_Retrasos'] / dist.sum() * 100
pct_inc = dist['Producto_Incorrecto_Faltante'] / dist.sum() * 100
print(f"\nDolor principal: Logistica_Retrasos ({pct_log:.1f}%) + Producto_Incorrecto_Faltante ({pct_inc:.1f}%) = {pct_log+pct_inc:.1f}%")
print("El problema no está en las categorías más vendidas — está en la cadena de entrega transversal a todo el catálogo.")
