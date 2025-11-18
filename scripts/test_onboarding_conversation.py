"""
Script para simular conversação de onboarding e avaliar tom conversacional.

Este script testa os 3 métodos core implementados no BLOCO 1:
- _extract_all_entities() - Extração oportunística
- _analyze_conversation_context() - Análise contextual
- _generate_contextual_response() - Geração adaptativa

Objetivo: Validar se o tom está natural (entrevista) vs robótico.
"""

import asyncio
import sys
import os

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_openai import ChatOpenAI
from src.agents.onboarding_agent import OnboardingAgent
from src.agents.client_profile_agent import ClientProfileAgent
from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ClientProfile
from src.graph.states import BSCState
from config.settings import settings


def print_turn(role: str, message: str):
    """Formata e imprime um turn da conversa."""
    separator = "=" * 80
    if role == "AGENT":
        print(f"\n{separator}")
        print(f"🤖 AGENTE BSC:")
        print(separator)
        print(message)
        print(separator)
    else:
        print(f"\n{'─' * 80}")
        print(f"👤 USUÁRIO:")
        print(f"{'─' * 80}")
        print(message)
        print(f"{'─' * 80}")


async def simulate_conversation():
    """Simula uma conversa completa de onboarding."""
    
    print("\n" + "=" * 80)
    print("SIMULAÇÃO DE ONBOARDING CONVERSACIONAL - AVALIAÇÃO DE TOM")
    print("=" * 80)
    print("\nCENÁRIO: Cliente iniciando diagnóstico BSC para sua empresa")
    print("OBJETIVO: Avaliar se tom está natural (entrevista) vs robótico\n")
    
    # Inicializar agentes
    llm = ChatOpenAI(
        model=settings.onboarding_llm_model,
        temperature=1.0,
        max_completion_tokens=settings.gpt5_max_completion_tokens
    )
    
    profile_agent = ClientProfileAgent(llm=llm)
    
    # Memória mock (não vamos salvar de verdade)
    memory = Mem0ClientWrapper(api_key="mock_key_for_testing")
    
    onboarding_agent = OnboardingAgent(
        llm=llm,
        client_profile_agent=profile_agent,
        memory_client=memory
    )
    
    # Inicializar state
    state = BSCState(
        client_id="test_simulation_001",
        client_profile=ClientProfile(),
        current_phase="ONBOARDING",
        messages=[],
        onboarding_progress={}
    )
    
    # Turn 1: Iniciar onboarding
    print("\n" + "🔄" * 40)
    print("TURN 1: Iniciando onboarding")
    print("🔄" * 40)
    
    result = onboarding_agent.start_onboarding("test_simulation_001", state)
    print_turn("AGENT", result["question"])
    
    # Turn 2: Usuário responde com informações da empresa
    user_message_1 = (
        "Olá! Sou da TechSolutions Brasil, uma empresa de tecnologia "
        "de médio porte com 150 funcionários. Atuamos no setor de software empresarial."
    )
    print_turn("USER", user_message_1)
    
    print("\n⏳ Processando resposta do usuário...")
    result = onboarding_agent.process_turn("test_simulation_001", user_message_1, state)
    print_turn("AGENT", result["question"])
    
    # Turn 3: Usuário menciona OBJETIVOS primeiro (teste de redirect)
    user_message_2 = (
        "Queremos crescer 30% nossa receita no próximo ano e expandir "
        "para o mercado enterprise. Também queremos melhorar nosso NPS para 80."
    )
    print_turn("USER", user_message_2)
    
    print("\n⏳ Processando resposta do usuário (objectives antes de challenges)...")
    result = onboarding_agent.process_turn("test_simulation_001", user_message_2, state)
    print_turn("AGENT", result["question"])
    
    # Turn 4: Usuário agora menciona challenges
    user_message_3 = (
        "Ok, nossos principais desafios são: alta rotatividade na equipe de desenvolvimento, "
        "baixa conversão de leads em vendas, e processos de onboarding de clientes muito lentos."
    )
    print_turn("USER", user_message_3)
    
    print("\n⏳ Processando resposta do usuário (challenges fornecidos)...")
    result = onboarding_agent.process_turn("test_simulation_001", user_message_3, state)
    print_turn("AGENT", result["question"])
    
    # Avaliação final
    print("\n" + "=" * 80)
    print("AVALIAÇÃO FINAL DO TOM CONVERSACIONAL")
    print("=" * 80)
    
    print("""
CRITÉRIOS DE AVALIAÇÃO:

1. TOM NATURAL vs ROBÓTICO
   - ❓ Respostas soam como um consultor humano real?
   - ❓ Ou parecem templates automáticos genéricos?

2. EMPATIA E PERSONALIZAÇÃO
   - ❓ Agente usa nome da empresa e contexto?
   - ❓ Ou faz perguntas genéricas sem considerar o contexto?

3. PROGRESSIVE DISCLOSURE
   - ❓ Faz UMA pergunta por vez?
   - ❓ Ou bombardeia com múltiplas perguntas?

4. REDIRECT SUAVE
   - ❓ Quando usuário mencionou objetivos primeiro, redirect foi educativo e suave?
   - ❓ Ou foi condescendente/autoritário?

5. LINGUAGEM
   - ❓ Evita clichês robóticos ("De acordo com", "Conforme mencionado")?
   - ❓ Usa linguagem conversacional natural?

---

INSTRUÇÕES PARA AVALIAÇÃO MANUAL:
1. Leia as 4 respostas do agente acima
2. Classifique cada critério: ✅ Natural | ⚠️ Neutro | ❌ Robótico
3. Sugira melhorias específicas se necessário

---
""")


if __name__ == "__main__":
    # Verificar se OpenAI API key está configurada
    if not settings.openai_api_key:
        print("\n❌ ERRO: OPENAI_API_KEY não configurada no .env")
        print("Este script requer API key real para testar GPT-5 mini.")
        sys.exit(1)
    
    print("✅ API Key configurada. Iniciando simulação com GPT-5 mini...\n")
    asyncio.run(simulate_conversation())

