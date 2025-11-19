"""
Teste Smoke: Validar refactor de 4 agentes BSC (remocao AgentExecutor)

Valida que os 4 agentes especializados funcionam corretamente apos refactor:
- financial_agent.py
- customer_agent.py  
- process_agent.py
- learning_agent.py

CONTEXTO: LangChain v1.0 deprecou AgentExecutor. Migramos para pattern moderno
usando LLM.bind_tools() diretamente.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_financial_agent_smoke():
    """Teste smoke: Financial Agent funciona pos-refactor."""
    from src.agents.financial_agent import FinancialAgent
    
    agent = FinancialAgent()
    
    # Validar estrutura basica
    assert agent.name == "Financial Agent"
    assert agent.perspective == "financeira"
    assert hasattr(agent, 'llm_with_tools'), "Deve ter llm_with_tools (pattern v1.0)"
    assert not hasattr(agent, 'executor'), "NAO deve ter executor (deprecated)"
    
    # Validar metodos disponiveis
    assert hasattr(agent, 'invoke'), "Deve ter metodo invoke()"
    assert hasattr(agent, 'ainvoke'), "Deve ter metodo ainvoke()"
    
    print("[OK] FinancialAgent: estrutura validada pos-refactor")


def test_customer_agent_smoke():
    """Teste smoke: Customer Agent funciona pos-refactor."""
    from src.agents.customer_agent import CustomerAgent
    
    agent = CustomerAgent()
    
    # Validar estrutura basica
    assert agent.name == "Customer Agent"
    assert agent.perspective == "cliente"
    assert hasattr(agent, 'llm_with_tools'), "Deve ter llm_with_tools (pattern v1.0)"
    assert not hasattr(agent, 'executor'), "NAO deve ter executor (deprecated)"
    
    # Validar metodos disponiveis
    assert hasattr(agent, 'invoke'), "Deve ter metodo invoke()"
    assert hasattr(agent, 'ainvoke'), "Deve ter metodo ainvoke()"
    
    print("[OK] CustomerAgent: estrutura validada pos-refactor")


def test_process_agent_smoke():
    """Teste smoke: Process Agent funciona pos-refactor."""
    from src.agents.process_agent import ProcessAgent
    
    agent = ProcessAgent()
    
    # Validar estrutura basica
    assert agent.name == "Process Agent"
    assert agent.perspective == "processos"
    assert hasattr(agent, 'llm_with_tools'), "Deve ter llm_with_tools (pattern v1.0)"
    assert not hasattr(agent, 'executor'), "NAO deve ter executor (deprecated)"
    
    # Validar metodos disponiveis
    assert hasattr(agent, 'invoke'), "Deve ter metodo invoke()"
    assert hasattr(agent, 'ainvoke'), "Deve ter metodo ainvoke()"
    
    print("[OK] ProcessAgent: estrutura validada pos-refactor")


def test_learning_agent_smoke():
    """Teste smoke: Learning Agent funciona pos-refactor."""
    from src.agents.learning_agent import LearningAgent
    
    agent = LearningAgent()
    
    # Validar estrutura basica
    assert agent.name == "Learning & Growth Agent"
    assert agent.perspective == "aprendizado"
    assert hasattr(agent, 'llm_with_tools'), "Deve ter llm_with_tools (pattern v1.0)"
    assert not hasattr(agent, 'executor'), "NAO deve ter executor (deprecated)"
    
    # Validar metodos disponiveis
    assert hasattr(agent, 'invoke'), "Deve ter metodo invoke()"
    assert hasattr(agent, 'ainvoke'), "Deve ter metodo ainvoke()"
    
    print("[OK] LearningAgent: estrutura validada pos-refactor")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTE SMOKE: Refactor 4 Agentes BSC (LangChain v1.0)")
    print("="*70 + "\n")
    
    test_financial_agent_smoke()
    test_customer_agent_smoke()
    test_process_agent_smoke()
    test_learning_agent_smoke()
    
    print("\n" + "="*70)
    print("[OK] TODOS OS 4 AGENTES VALIDADOS - Refactor bem-sucedido!")
    print("="*70 + "\n")

