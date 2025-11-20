"""
Script para remover TODOS os emojis detectados pelo pre-commit.
"""
import re
import sys
from pathlib import Path

# Mapeamento de emojis Unicode para ASCII
EMOJI_REPLACEMENTS = {
    '\u2192': '->',      # SETA DIREITA
    '\u2190': '<-',      # SETA ESQUERDA
    '\u2194': '<->',     # SETA BIDIRECIONAL
    '\u2705': '[OK]',    # CHECKMARK VERDE
    '\u2713': '[OK]',    # CHECKMARK SIMPLES
    '\u2717': '[X]',     # CROSS MARK
    '\u274C': '[ERRO]',  # X VERMELHO
    '\u26A0\uFE0F': '[WARN]',  # AVISO
    '\u26A0': '[WARN]',  # AVISO (sem variation selector)
    '\u26A1': '[FAST]',  # RAIO
    '\u1F4CA': '[CHART]',  # GRAFICO
    '\u1F4CB': '[CLIPBOARD]',  # PRANCHETA
    '\u1F4C8': '[TRENDING]',  # GRAFICO SUBINDO
    '\u1F4C5': '[CALENDAR]',  # CALENDARIO
    '\u1F4DD': '[MEMO]',  # MEMO
    '\u1F3AF': '[TARGET]',  # ALVO
    '\u1F534': '[HIGH]',  # CIRCULO VERMELHO
    '\u1F7E1': '[MEDIUM]',  # CIRCULO AMARELO
    '\u1F7E2': '[LOW]',  # CIRCULO VERDE
    '\u1F527': '[TOOL]',  # FERRAMENTA
    '\u1FAB6': '[FEATHER]',  # PENA
    '\u1F393': '[LEARN]',  # CHAPEU GRADUACAO
    '\u1F4E4': '[OUTPUT]',  # CAIXA SAIDA
    '\u1F4DA': '[BOOK]',  # LIVRO
    '\u1F916': '[BOT]',  # ROBO
    '\u1F464': '[USER]',  # USUARIO
    '\u1F504': '[LOOP]',  # LOOP
    '\u2753': '[?]',  # INTERROGACAO
    '\u23F1\uFE0F': '[TIMER]',  # CRONOMETRO (com variation selector)
    '\u23F1': '[TIMER]',  # CRONOMETRO
    '\uFE0F': '',  # VARIATION SELECTOR (remover)
    '\u0304': '',  # COMBINING MACRON (remover)
}

def remove_emojis_from_file(file_path: Path) -> bool:
    """Remove emojis de um arquivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Substituir emojis conhecidos
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)
        
        # Remover qualquer outro emoji Unicode (U+1F300 a U+1F9FF, U+2600 a U+26FF)
        content = re.sub(r'[\U0001F300-\U0001F9FF\U00002600-\U000026FF]', '[EMOJI]', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            print(f"[OK] {file_path}")
            return True
        return False
    
    except Exception as e:
        print(f"[ERRO] {file_path}: {e}")
        return False

def main():
    """Remove emojis de todos os arquivos Python e Markdown."""
    root = Path(__file__).parent.parent
    
    # Buscar arquivos com emojis
    patterns = ['**/*.py', '**/*.md']
    files_processed = 0
    files_modified = 0
    
    for pattern in patterns:
        for file_path in root.glob(pattern):
            # Ignorar venv e node_modules
            if 'venv' in str(file_path) or 'node_modules' in str(file_path):
                continue
            
            files_processed += 1
            if remove_emojis_from_file(file_path):
                files_modified += 1
    
    print(f"\n[SUMMARY]")
    print(f"  Arquivos processados: {files_processed}")
    print(f"  Arquivos modificados: {files_modified}")
    
    return 0 if files_modified == 0 else 1

if __name__ == '__main__':
    sys.exit(main())

