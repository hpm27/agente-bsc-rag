"""
Inspeciona ground truth do benchmark vs documentos reais no Qdrant.

Objetivo: Entender por que recall/precision estão em 0%.
"""

import sys
import json
from pathlib import Path
from collections import Counter

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.rag.retriever import BSCRetriever


def inspect_ground_truth():
    """Inspeciona documentos disponíveis vs ground truth esperado."""
    
    # Carregar benchmark queries
    benchmark_file = project_root / "tests" / "benchmark_queries.json"
    with open(benchmark_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    queries = data["queries"]
    
    # Inicializar retriever
    retriever = BSCRetriever()
    
    print("=" * 80)
    print("INSPEÇÃO GROUND TRUTH vs DOCUMENTOS REAIS")
    print("=" * 80)
    print()
    
    # Inspecionar metadados disponíveis
    print("[1/4] Inspecionando metadados disponíveis nos documentos...")
    query = queries[0]["query"]
    sample_docs = retriever.retrieve(query, k=5)
    
    print("Metadados do primeiro documento:")
    if sample_docs:
        print(json.dumps(sample_docs[0].metadata, indent=2, ensure_ascii=False))
    print()
    
    # Coletar todos os sources únicos disponíveis
    print("[2/4] Coletando identificadores únicos de documentos recuperados...")
    all_sources = set()
    metadata_fields = set()
    
    for query_data in queries[:5]:  # Sample 5 queries
        query = query_data["query"]
        docs = retriever.retrieve(query, k=20)
        for doc in docs:
            # Coletar todos os campos de metadata
            metadata_fields.update(doc.metadata.keys())
            
            # Tentar diferentes campos para identificar documento
            doc_id = (
                doc.metadata.get("source", "") or 
                doc.metadata.get("title", "") or
                doc.metadata.get("document", "") or
                doc.metadata.get("filename", "") or
                doc.metadata.get("file_name", "") or
                doc.metadata.get("book", "") or
                ""
            )
            all_sources.add(doc_id)
    
    print(f"Campos de metadata disponíveis: {sorted(metadata_fields)}")
    print(f"Total de identificadores únicos encontrados: {len(all_sources)}")
    print()
    
    # Mostrar samples de identificadores
    print("Samples de identificadores reais (10 primeiros):")
    for i, source in enumerate(sorted(all_sources)[:10], 1):
        print(f"  {i}. '{source}'")
    print()
    
    # Comparar com ground truth
    print("[3/4] Comparando com ground truth esperado...")
    print()
    
    ground_truth_docs = set()
    for query_data in queries:
        for gt_doc in query_data.get("ground_truth_docs", []):
            ground_truth_docs.add(gt_doc)
    
    print(f"Total de documentos no ground truth: {len(ground_truth_docs)}")
    print("Ground truth esperado:")
    for i, gt_doc in enumerate(sorted(ground_truth_docs), 1):
        print(f"  {i}. {gt_doc}")
    print()
    
    # Verificar matches
    print("[4/4] Verificando matches fuzzy...")
    print()
    
    from difflib import SequenceMatcher
    
    def fuzzy_match(doc_source, ground_truth, threshold=0.70):
        """Testa fuzzy matching."""
        doc_normalized = doc_source.lower().replace("_", " ").replace("-", " ")
        gt_normalized = ground_truth.lower().replace("_", " ").replace("-", " ")
        
        # Match direto
        if gt_normalized in doc_normalized:
            return True, 1.0, "substring"
        
        # Fuzzy match completo
        similarity = SequenceMatcher(None, doc_normalized, gt_normalized).ratio()
        if similarity >= threshold:
            return True, similarity, "full_fuzzy"
        
        # Fuzzy match apenas filename
        doc_filename = doc_normalized.split("/")[-1].split("\\")[-1]
        filename_similarity = SequenceMatcher(None, doc_filename, gt_normalized).ratio()
        if filename_similarity >= threshold:
            return True, filename_similarity, "filename_fuzzy"
        
        return False, max(similarity, filename_similarity), "no_match"
    
    # Testar cada ground truth doc
    matches = []
    no_matches = []
    
    for gt_doc in sorted(ground_truth_docs):
        found = False
        best_match = None
        best_score = 0.0
        
        for source in all_sources:
            is_match, score, match_type = fuzzy_match(source, gt_doc)
            if is_match:
                found = True
                if score > best_score:
                    best_score = score
                    best_match = (source, score, match_type)
        
        if found:
            matches.append((gt_doc, best_match))
            print(f"[OK] '{gt_doc}'")
            print(f"     -> MATCH: '{best_match[0]}'")
            print(f"     -> Score: {best_match[1]:.2%} ({best_match[2]})")
        else:
            no_matches.append(gt_doc)
            print(f"[FAIL] '{gt_doc}' -> NENHUM MATCH ENCONTRADO")
        print()
    
    # Sumário
    print("=" * 80)
    print("SUMÁRIO")
    print("=" * 80)
    print(f"Ground truth docs: {len(ground_truth_docs)}")
    print(f"Matches encontrados: {len(matches)} ({len(matches)/len(ground_truth_docs)*100:.1f}%)")
    print(f"Sem match: {len(no_matches)} ({len(no_matches)/len(ground_truth_docs)*100:.1f}%)")
    print()
    
    if no_matches:
        print("Documentos SEM MATCH:")
        for gt_doc in no_matches:
            print(f"  - {gt_doc}")
        print()
        print("AÇÃO NECESSÁRIA:")
        print("  1. Verificar se documentos existem no Qdrant")
        print("  2. Ajustar nomes no ground truth para bater com sources reais")
        print("  3. Reduzir threshold de fuzzy matching se necessário")


if __name__ == "__main__":
    inspect_ground_truth()

