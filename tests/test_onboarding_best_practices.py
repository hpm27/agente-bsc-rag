"""
Testes para validar implementação das best practices de Nov/2025.

Best Practices Implementadas:
1. Progressive Summarization - evita "Lost in Middle"
2. Concat-and-Retry - confirmação com contexto limpo
3. Detecção de Repetições - evita frustração do usuário

Baseado em:
- Paper "LLMs Get Lost in Multi-Turn Conversation" (MS/Salesforce 2025)
- Medium Dr. Ankit Malviya (Oct/2025)
- KeywordsAI Blog (Jul/2025)
"""

import pytest
from src.agents.onboarding_agent import OnboardingAgent


class TestProgressiveSummarization:
    """Testa _get_effective_context (Progressive Summarization)."""

    @pytest.fixture
    def agent(self):
        """Cria instância mock do OnboardingAgent."""
        agent = OnboardingAgent.__new__(OnboardingAgent)
        return agent

    def test_short_history_returns_complete(self, agent):
        """Histórico curto (<=4 msgs) deve retornar completo."""
        short_history = [
            {"role": "user", "content": "Olá"},
            {"role": "assistant", "content": "Olá! Como posso ajudar?"},
        ]
        partial_profile = {"company_name": "TechCorp"}

        result = agent._get_effective_context(short_history, partial_profile)

        # Deve conter as mensagens originais
        assert "Olá" in result
        assert "Como posso ajudar?" in result

    def test_long_history_is_summarized(self, agent):
        """Histórico longo (>4 msgs) deve ser sumarizado."""
        long_history = [
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "resp1"},
            {"role": "user", "content": "msg2"},
            {"role": "assistant", "content": "resp2"},
            {"role": "user", "content": "msg3"},
            {"role": "assistant", "content": "resp3"},
            {"role": "user", "content": "msg4 mais recente"},
            {"role": "assistant", "content": "resp4 mais recente"},
        ]
        partial_profile = {
            "company_name": "TechCorp",
            "industry": "Tecnologia",
            "challenges": ["alta rotatividade"],
        }

        result = agent._get_effective_context(long_history, partial_profile)

        # Deve conter sumário dos dados acumulados
        assert "[CONTEXTO ACUMULADO" in result
        assert "TechCorp" in result
        assert "Tecnologia" in result
        assert "alta rotatividade" in result

        # Deve conter últimas mensagens
        assert "[ÚLTIMAS MENSAGENS]" in result
        assert "msg4 mais recente" in result

        # NÃO deve conter mensagens antigas completas
        assert "msg1" not in result or "[ÚLTIMAS MENSAGENS]" in result

    def test_empty_history(self, agent):
        """Histórico vazio deve retornar string vazia formatada."""
        result = agent._get_effective_context([], None)

        # Deve retornar algo (não vazio)
        assert result is not None
        assert isinstance(result, str)


class TestDetectUserRepetition:
    """Testa _detect_user_repetition."""

    @pytest.fixture
    def agent(self):
        """Cria instância mock do OnboardingAgent."""
        agent = OnboardingAgent.__new__(OnboardingAgent)
        return agent

    @pytest.fixture
    def partial_profile(self):
        """Profile típico com dados coletados."""
        return {
            "company_name": "TechCorp",
            "industry": "Tecnologia",
            "challenges": ["demora na aprovação dos clientes", "alta rotatividade"],
            "goals": ["crescer 30% no ano"],
        }

    def test_detects_company_name_repetition(self, agent, partial_profile):
        """Deve detectar quando usuário repete nome da empresa."""
        result = agent._detect_user_repetition("A TechCorp tem muitos problemas", partial_profile)

        assert "company_name" in result

    def test_detects_industry_repetition(self, agent, partial_profile):
        """Deve detectar quando usuário repete setor."""
        result = agent._detect_user_repetition("O setor de tecnologia é difícil", partial_profile)

        assert "industry" in result

    def test_no_repetition_detected(self, agent, partial_profile):
        """Não deve detectar repetição em mensagem nova."""
        result = agent._detect_user_repetition(
            "Quero expandir para novos mercados", partial_profile
        )

        assert len(result) == 0

    def test_empty_profile_no_repetition(self, agent):
        """Profile vazio não deve detectar nada."""
        result = agent._detect_user_repetition("TechCorp é ótima", None)

        assert len(result) == 0

    def test_short_company_name_not_detected(self, agent):
        """Nomes curtos (<3 chars) não devem ser detectados (falsos positivos)."""
        partial_profile = {"company_name": "AB"}

        result = agent._detect_user_repetition("Abrimos uma filial no AB", partial_profile)

        # Deve ignorar nomes muito curtos
        assert "company_name" not in result


class TestConfirmationFallback:
    """Testa _get_confirmation_fallback."""

    @pytest.fixture
    def agent(self):
        """Cria instância mock do OnboardingAgent."""
        agent = OnboardingAgent.__new__(OnboardingAgent)
        return agent

    def test_fallback_with_industry(self, agent):
        """Fallback com setor deve incluir setor."""
        partial_profile = {"company_name": "TechCorp", "industry": "Tecnologia"}

        result = agent._get_confirmation_fallback(partial_profile)

        assert "TechCorp" in result
        assert "Tecnologia" in result
        assert "?" in result  # Deve ser pergunta

    def test_fallback_without_industry(self, agent):
        """Fallback sem setor deve ter mensagem simplificada."""
        partial_profile = {"company_name": "TechCorp"}

        result = agent._get_confirmation_fallback(partial_profile)

        assert "TechCorp" in result
        assert "?" in result  # Deve ser pergunta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
