import pandas as pd
import re
import sys
from pathlib import Path
from collections import Counter
from langchain_ollama import OllamaLLM

DATA_DIR = Path(__file__).parent.parent / 'data'
CHECKPOINT_PATH = Path(__file__).parent.parent / 'data' / 'malas_experiencias_clasificadas.csv'

MODEL = "granite4:3b"
TAXONOMY = [
    "Logistica_Retrasos",
    "Calidad_Producto",
    "Producto_Incorrecto_Faltante",
    "Reembolso_Atencion_Cliente",
    "Problema_Fiscal_Burocracia",
    "Otro",
]
TAXONOMY_SET = set(TAXONOMY)

PROMPT_TEMPLATE = """You are a classifier. Classify this Portuguese e-commerce customer complaint into exactly one category.

Categories:
- Logistica_Retrasos: late delivery, not received, shipping delays, carrier issues
- Calidad_Producto: defective, bad quality, broken, damaged product
- Producto_Incorrecto_Faltante: wrong item sent, missing item, different from what was ordered
- Reembolso_Atencion_Cliente: refund request, no customer service response, money back
- Problema_Fiscal_Burocracia: invoice issues, nota fiscal, tax documents, billing
- Otro: anything that does not fit the above

Customer review (in Portuguese): {comment}

Reply with ONLY the category name from the list above, nothing else. Do not explain."""


def classify_comment(llm, comment: str) -> str:
    prompt = PROMPT_TEMPLATE.format(comment=comment.strip())
    response = llm.invoke(prompt).strip()
    # Buscar la categoría en la respuesta (por si el modelo añade texto extra)
    for cat in TAXONOMY:
        if cat.lower() in response.lower():
            return cat
    return "Otro"


# =============================================================================
# CARGA Y FILTRO (igual que antes)
# =============================================================================
order_reviews_dataset = pd.read_csv(DATA_DIR / 'order_reviews_dataset.csv')

malas_experiencias = order_reviews_dataset[
    order_reviews_dataset['review_score'].isin([1, 2]) &
    order_reviews_dataset['review_comment_message'].notna()
].copy().reset_index(drop=True)

print(f"Corpus de quejas: {len(malas_experiencias)} comentarios")

# =============================================================================
# MODO: 'test' (10 comentarios) o 'full' (todos)
# Pasar argumento: python script.py test  |  python script.py full
# =============================================================================
MODE = sys.argv[1] if len(sys.argv) > 1 else 'test'

if MODE == 'test':
    sample = malas_experiencias.sample(10, random_state=42).copy()
    print(f"\n{'='*70}")
    print("PASO 3 (TEST): Clasificación con granite4:3b — 10 comentarios")
    print("="*70)

    llm = OllamaLLM(model=MODEL, temperature=0)

    results = []
    for i, row in sample.iterrows():
        comment = row['review_comment_message']
        category = classify_comment(llm, comment)
        results.append({'comment': comment[:120], 'score': row['review_score'], 'category': category})
        print(f"[{len(results):2d}/10] score={row['review_score']} | {category}")
        print(f"       \"{comment[:100]}\"")

    print("\n--- Resumen del test ---")
    test_df = pd.DataFrame(results)
    print(test_df['category'].value_counts().to_string())

elif MODE == 'full':
    print(f"\n{'='*70}")
    print("PASO 3 (FULL): Clasificación con granite4:3b — todos los comentarios")
    print("="*70)

    # Reanudar desde checkpoint si existe
    if CHECKPOINT_PATH.exists():
        already_done = pd.read_csv(CHECKPOINT_PATH)
        done_ids = set(already_done['review_id'])
        pending = malas_experiencias[~malas_experiencias['review_id'].isin(done_ids)].copy()
        print(f"Checkpoint encontrado: {len(already_done)} ya clasificados, {len(pending)} pendientes")
    else:
        already_done = pd.DataFrame()
        pending = malas_experiencias.copy()
        print(f"Sin checkpoint. Clasificando {len(pending)} comentarios...")

    llm = OllamaLLM(model=MODEL, temperature=0)
    new_results = []
    total = len(pending)
    CHECKPOINT_EVERY = 200

    for idx, (_, row) in enumerate(pending.iterrows(), start=1):
        category = classify_comment(llm, row['review_comment_message'])
        new_results.append({
            'review_id': row['review_id'],
            'order_id': row['order_id'],
            'review_score': row['review_score'],
            'review_comment_message': row['review_comment_message'],
            'pain_point_category': category,
        })

        if idx % CHECKPOINT_EVERY == 0 or idx == total:
            chunk = pd.DataFrame(new_results)
            combined = pd.concat([already_done, chunk], ignore_index=True) if not already_done.empty else chunk
            combined.to_csv(CHECKPOINT_PATH, index=False)
            already_done = combined
            new_results = []
            pct = idx / total * 100
            print(f"  [{idx:5d}/{total}] {pct:.1f}% completado — checkpoint guardado")

    print(f"\nClasificación completa. Resultado en: {CHECKPOINT_PATH}")
    final = pd.read_csv(CHECKPOINT_PATH)
    print("\nDistribución de pain_point_category:")
    print(final['pain_point_category'].value_counts().to_string())
