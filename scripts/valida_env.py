"""
Script de validacao rapida do arquivo .env
Verifica se todas as configuracoes obrigatorias estao presentes e validas.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Adicionar root ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def check_api_key(key_name: str, key_value: str) -> Tuple[bool, str]:
    """Valida uma API key."""
    if not key_value or key_value.startswith("your_"):
        return False, f"[ERRO] {key_name} nao configurada (ainda usa placeholder)"
    
    # Validacoes basicas de formato
    if key_name == "OPENAI_API_KEY":
        if not key_value.startswith("sk-"):
            return False, f"[ERRO] {key_name} invalida (deve comecar com 'sk-')"
    
    elif key_name == "ANTHROPIC_API_KEY":
        if not key_value.startswith("sk-ant-"):
            return False, f"[ERRO] {key_name} invalida (deve comecar com 'sk-ant-')"
    
    return True, f"[OK] {key_name} configurada"


def main():
    """Funcao principal de validacao."""
    print("=" * 70)
    print("[CHECK] Validando configuracao .env do Agente BSC RAG")
    print("=" * 70)
    print()
    
    # Carregar .env
    env_path = root_dir / ".env"
    
    if not env_path.exists():
        print("[ERRO] Arquivo .env nao encontrado!")
        print(f"[INFO] Esperado em: {env_path}")
        print("[INFO] Execute: Copy-Item .env.example .env")
        sys.exit(1)
    
    print(f"[OK] Arquivo .env encontrado: {env_path}")
    print()
    
    # Carregar variaveis de ambiente
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    errors: List[str] = []
    warnings: List[str] = []
    ok_messages: List[str] = []
    
    # ==============================================================================
    # 1. API Keys Obrigatorias
    # ==============================================================================
    
    print("[1/6] Validando API Keys Obrigatorias...")
    print("-" * 70)
    
    # OpenAI (sempre necessaria)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    is_valid, msg = check_api_key("OPENAI_API_KEY", openai_key)
    if is_valid:
        ok_messages.append(msg)
    else:
        errors.append(msg)
    
    # Cohere (sempre necessaria)
    cohere_key = os.getenv("COHERE_API_KEY", "")
    is_valid, msg = check_api_key("COHERE_API_KEY", cohere_key)
    if is_valid:
        ok_messages.append(msg)
    else:
        errors.append(msg)
    
    print()
    
    # ==============================================================================
    # 2. Modelo LLM e API Key Correspondente
    # ==============================================================================
    
    print("[2/6] Validando Modelo LLM...")
    print("-" * 70)
    
    default_model = os.getenv("DEFAULT_LLM_MODEL", "")
    
    if not default_model:
        errors.append("[ERRO] DEFAULT_LLM_MODEL nao configurado")
    else:
        ok_messages.append(f"[OK] Modelo LLM: {default_model}")
        
        # Se for Claude, precisa da chave Anthropic
        if default_model.startswith("claude-"):
            anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
            is_valid, msg = check_api_key("ANTHROPIC_API_KEY", anthropic_key)
            if not is_valid:
                errors.append(
                    f"[ERRO] ANTHROPIC_API_KEY necessaria para modelo {default_model}"
                )
            else:
                ok_messages.append(msg)
        
        # Se for GPT, ja validamos OpenAI acima
        elif default_model.startswith("gpt-"):
            ok_messages.append("[OK] Modelo GPT usa OPENAI_API_KEY (ja validada)")
        else:
            warnings.append(
                f"[WARN] Modelo '{default_model}' nao reconhecido "
                "(deve comecar com 'gpt-' ou 'claude-')"
            )
    
    print()
    
    # ==============================================================================
    # 3. Vector Store Configuration
    # ==============================================================================
    
    print("[3/6] Validando Vector Store...")
    print("-" * 70)
    
    vector_store_type = os.getenv("VECTOR_STORE_TYPE", "")
    
    if vector_store_type not in ["qdrant", "weaviate", "redis"]:
        errors.append(
            f"[ERRO] VECTOR_STORE_TYPE invalido: '{vector_store_type}' "
            "(deve ser 'qdrant', 'weaviate' ou 'redis')"
        )
    else:
        ok_messages.append(f"[OK] Vector Store: {vector_store_type}")
        
        # Validar configuracoes especificas
        if vector_store_type == "qdrant":
            host = os.getenv("QDRANT_HOST", "localhost")
            port = os.getenv("QDRANT_PORT", "6333")
            ok_messages.append(f"[OK] Qdrant: {host}:{port}")
            warnings.append(
                "[WARN] Lembre-se de iniciar Qdrant: docker-compose up -d qdrant"
            )
        
        elif vector_store_type == "weaviate":
            host = os.getenv("WEAVIATE_HOST", "localhost")
            port = os.getenv("WEAVIATE_PORT", "8080")
            ok_messages.append(f"[OK] Weaviate: {host}:{port}")
            warnings.append(
                "[WARN] Lembre-se de iniciar Weaviate: docker-compose up -d weaviate"
            )
        
        elif vector_store_type == "redis":
            host = os.getenv("REDIS_HOST", "localhost")
            port = os.getenv("REDIS_PORT", "6379")
            ok_messages.append(f"[OK] Redis: {host}:{port}")
            warnings.append(
                "[WARN] Lembre-se de iniciar Redis: docker-compose up -d redis"
            )
    
    print()
    
    # ==============================================================================
    # 4. Embedding Cache
    # ==============================================================================
    
    print("[4/6] Validando Embedding Cache...")
    print("-" * 70)
    
    cache_enabled = os.getenv("EMBEDDING_CACHE_ENABLED", "True").lower() == "true"
    
    if cache_enabled:
        cache_dir = os.getenv("EMBEDDING_CACHE_DIR", ".cache/embeddings")
        cache_ttl = os.getenv("EMBEDDING_CACHE_TTL_DAYS", "30")
        cache_max_size = os.getenv("EMBEDDING_CACHE_MAX_SIZE_GB", "5")
        
        ok_messages.append("[OK] Embedding cache ATIVADO")
        ok_messages.append(f"[OK] Cache dir: {cache_dir}")
        ok_messages.append(f"[OK] Cache TTL: {cache_ttl} dias")
        ok_messages.append(f"[OK] Cache max size: {cache_max_size} GB")
    else:
        warnings.append(
            "[WARN] Embedding cache DESATIVADO (vai processar embeddings toda vez)"
        )
    
    print()
    
    # ==============================================================================
    # 5. Contextual Retrieval
    # ==============================================================================
    
    print("[5/6] Validando Contextual Retrieval...")
    print("-" * 70)
    
    contextual_enabled = os.getenv("ENABLE_CONTEXTUAL_RETRIEVAL", "True").lower() == "true"
    
    if contextual_enabled:
        contextual_provider = os.getenv("CONTEXTUAL_PROVIDER", "openai")
        
        if contextual_provider not in ["openai", "anthropic"]:
            errors.append(
                f"[ERRO] CONTEXTUAL_PROVIDER invalido: '{contextual_provider}' "
                "(deve ser 'openai' ou 'anthropic')"
            )
        else:
            ok_messages.append(f"[OK] Contextual Retrieval: {contextual_provider}")
            
            if contextual_provider == "anthropic":
                # Verificar se tem chave Anthropic
                anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
                if not anthropic_key or anthropic_key.startswith("your_"):
                    errors.append(
                        "[ERRO] ANTHROPIC_API_KEY necessaria para "
                        "CONTEXTUAL_PROVIDER=anthropic"
                    )
    else:
        warnings.append("[WARN] Contextual Retrieval DESATIVADO")
    
    print()
    
    # ==============================================================================
    # 6. Diretorios
    # ==============================================================================
    
    print("[6/6] Validando Diretorios...")
    print("-" * 70)
    
    data_dir = Path(os.getenv("DATA_DIR", "./data"))
    literature_dir = Path(os.getenv("LITERATURE_DIR", "./data/bsc_literature"))
    models_dir = Path(os.getenv("MODELS_DIR", "./models"))
    logs_dir = Path(os.getenv("LOGS_DIR", "./logs"))
    
    for dir_path, dir_name in [
        (data_dir, "DATA_DIR"),
        (literature_dir, "LITERATURE_DIR"),
        (models_dir, "MODELS_DIR"),
        (logs_dir, "LOGS_DIR"),
    ]:
        if dir_path.exists():
            ok_messages.append(f"[OK] {dir_name}: {dir_path} (existe)")
        else:
            warnings.append(
                f"[WARN] {dir_name}: {dir_path} (nao existe, sera criado automaticamente)"
            )
    
    # Verificar se tem documentos BSC
    if literature_dir.exists():
        docs = list(literature_dir.glob("*.md")) + list(literature_dir.glob("*.pdf"))
        if docs:
            ok_messages.append(
                f"[OK] {len(docs)} documentos BSC encontrados em {literature_dir}"
            )
        else:
            warnings.append(
                f"[WARN] Nenhum documento BSC encontrado em {literature_dir}"
            )
    
    print()
    
    # ==============================================================================
    # Resumo Final
    # ==============================================================================
    
    print()
    print("=" * 70)
    print("[RESUMO] Validacao Completa")
    print("=" * 70)
    print()
    
    # Mostrar mensagens OK
    if ok_messages:
        print(f"[OK] {len(ok_messages)} validacoes OK:")
        for msg in ok_messages:
            print(f"  {msg}")
        print()
    
    # Mostrar warnings
    if warnings:
        print(f"[WARN] {len(warnings)} avisos:")
        for msg in warnings:
            print(f"  {msg}")
        print()
    
    # Mostrar erros
    if errors:
        print(f"[ERRO] {len(errors)} erros encontrados:")
        for msg in errors:
            print(f"  {msg}")
        print()
        print("[ERRO] Corrija os erros acima antes de executar o sistema!")
        print()
        print("Documentacao: CONFIGURACAO_RAPIDA.md")
        sys.exit(1)
    else:
        print("[OK] Nenhum erro encontrado!")
        print()
        print("[CHECK] Proximos passos:")
        print("  1. Iniciar vector store: docker-compose up -d")
        print("  2. Indexar documentos: python scripts/build_knowledge_base.py")
        print("  3. Iniciar interface: streamlit run app/main.py")
        print()
        print("Documentacao: CONFIGURACAO_RAPIDA.md")
        sys.exit(0)


if __name__ == "__main__":
    main()

