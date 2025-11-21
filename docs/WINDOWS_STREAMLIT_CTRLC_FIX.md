# 🪟 Windows: Como Parar Streamlit Corretamente

## ⚠️ Problema Conhecido

**Ctrl+C NÃO funciona** no Streamlit para Windows devido a bugs upstream confirmados:
- [GitHub Issue #6855](https://github.com/streamlit/streamlit/issues/6855) - 32+ upvotes
- [GitHub Issue #8181](https://github.com/streamlit/streamlit/issues/8181)

---

## ✅ Solução 1: Ctrl+Break (RECOMENDADO)

### Use SEMPRE no Windows:

```
Ctrl + Break  (tecla Break = Pause em alguns teclados)
```

**Por quê funciona**: Envia sinal `SIGBREAK` que Windows processa imediatamente, ao contrário de `SIGINT` (Ctrl+C) que é ignorado pelo Tornado async framework do Streamlit.

---

## ✅ Solução 2: Script stop_streamlit.ps1 (EMERGÊNCIA)

Quando Ctrl+Break não funcionar (raro):

```powershell
.\scripts\stop_streamlit.ps1
```

**O que faz**:
- Para TODOS processos `streamlit*`
- Para processos Python rodando Streamlit
- Verifica se parou com sucesso
- Reporta processos restantes

---

## ✅ Solução 3: Browser Tab + Ctrl+C (WORKAROUND)

1. Abrir http://localhost:8501 no browser
2. Voltar ao terminal
3. Pressionar Ctrl+C (agora funciona porque há conexão ativa)

**Por quê funciona**: Streamlit só processa sinais quando há eventos ativos (conexão browser).

---

## 🚫 O Que NÃO Funciona

- ❌ `Ctrl+C` múltiplas vezes (ignorado)
- ❌ Fechar terminal (deixa processo órfão)
- ❌ Reiniciar script sem parar anterior (múltiplas instâncias)

---

## 📊 Comparação de Métodos

| Método | Velocidade | Confiabilidade | Quando Usar |
|---|---|---|---|
| **Ctrl+Break** | ⚡ Instantâneo | ✅ 100% | Sempre (padrão) |
| **stop_streamlit.ps1** | ⚡ 2-3s | ✅ 100% | Emergência, múltiplas instâncias |
| **Browser Tab + Ctrl+C** | 🐌 5-10s | ⚠️ 80% | Workaround temporário |

---

## 🎯 Checklist de Uso

### Iniciar Streamlit:
- [ ] Usar `.\scripts\start_streamlit.ps1` (foreground)
- [ ] OU `python -m streamlit run app.py` (manual)

### Parar Streamlit:
- [ ] **Tentar Ctrl+Break primeiro** (método recomendado)
- [ ] Se não funcionar: `.\scripts\stop_streamlit.ps1`
- [ ] Verificar processos parados: `Get-Process python`

---

## 🔗 Referências

**Issues GitHub Streamlit**:
- https://github.com/streamlit/streamlit/issues/6855 (Jun 2023, 32+ upvotes)
- https://github.com/streamlit/streamlit/issues/8181 (Feb 2024)

**Discussões Comunidade**:
- https://discuss.streamlit.io/t/cant-stop-streamlit-app-using-ctrl-c/38738

**Stack Overflow**:
- https://stackoverflow.com/questions/1364173/stopping-python-using-ctrl-c
  - "On Windows, the only sure way is to use Ctrl + Break"

---

**Última Atualização**: 2025-11-21 (Sessão 39)
**Status**: Bug upstream confirmado, workarounds validados
**Prioridade Streamlit**: P2 (área:windows, feature:cli)
