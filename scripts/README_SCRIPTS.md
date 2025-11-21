# 📁 Scripts do Projeto BSC RAG Agent

## 🎯 Scripts PRINCIPAIS (Use estes!)

### 1. `start_streamlit.ps1`
**Uso básico - Iniciar aplicação rapidamente**
```powershell
.\scripts\start_streamlit.ps1
```
- ✅ Inicia o Streamlit rapidamente
- ✅ Configura PYTHONPATH
- ✅ Sem mensagens verbosas

### 2. `restart_streamlit.ps1`
**Uso completo - Reiniciar com limpeza de cache**
```powershell
.\scripts\restart_streamlit.ps1
```
- ✅ Para processos antigos
- ✅ Limpa cache Streamlit
- ✅ Limpa __pycache__
- ✅ Mostra todas as correções aplicadas
- ✅ Mensagens detalhadas de debug

## 📋 Quando usar cada um?

| Situação | Script Recomendado |
|----------|--------------------|
| **Primeira vez do dia** | `start_streamlit.ps1` |
| **Após fazer mudanças no código** | `restart_streamlit.ps1` |
| **Problemas/erros estranhos** | `restart_streamlit.ps1` |
| **Desenvolvimento rápido** | `start_streamlit.ps1` |

## 🔧 Scripts Python Utilitários

| Script | Descrição |
|--------|-----------|
| `clear_mem0_database.py` | Limpa base de dados Mem0 |
| `reset_mem0_complete.py` | Reset completo Mem0 |
| `test_loop_fix.py` | Testa correção de loop infinito |
| `validate_setup.py` | Valida configuração do ambiente |
| `build_knowledge_base.py` | Constrói base de conhecimento RAG |

## 📦 Pasta old_scripts_backup/

Scripts antigos de correções específicas foram movidos para backup.
Não precisam ser usados - todas as correções já estão aplicadas!

## ⚠️ IMPORTANTE

- **SEMPRE use** `start_streamlit.ps1` ou `restart_streamlit.ps1`
- **NÃO use** scripts da pasta old_scripts_backup (obsoletos)
- **PowerShell** é necessário para executar scripts .ps1

## 💡 Dicas

1. Se o Streamlit não abrir, verifique se a porta 8501 está livre
2. Se houver erro de módulo, use `restart_streamlit.ps1` (limpa cache)
3. Menu lateral aparece clicando no ">" no canto superior esquerdo

---

**Última atualização:** 2025-11-21
**Versão:** Scripts consolidados e simplificados
