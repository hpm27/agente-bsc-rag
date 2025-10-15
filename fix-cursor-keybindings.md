# Como Resetar Atalhos do Cursor

## Método 1: Via Interface

1. Abra o Cursor
2. Pressione `Ctrl + Shift + P` (Command Palette)
3. Digite: `Preferences: Open Keyboard Shortcuts`
4. Procure por:
   - `copy` → Deve estar mapeado para `Ctrl+C`
   - `paste` → Deve estar mapeado para `Ctrl+V`
   - `cut` → Deve estar mapeado para `Ctrl+X`

5. Se estiver diferente, clique com botão direito → `Reset Keybinding`

---

## Método 2: Verificar arquivo de configuração

1. Pressione `Ctrl + Shift + P`
2. Digite: `Preferences: Open User Settings (JSON)`
3. Procure por `"keybindings"` ou `"keyboard.dispatch"`
4. Se houver algo como:
   ```json
   "keyboard.dispatch": "keyCode"
   ```
   Mude para:
   ```json
   "keyboard.dispatch": "code"
   ```

---

## Método 3: Recarregar janela do Cursor

1. `Ctrl + Shift + P`
2. Digite: `Developer: Reload Window`
3. Teste Ctrl+C/V novamente

---

## Método 4: Modo Safe (desabilita extensões temporariamente)

1. Feche o Cursor
2. Abra o PowerShell
3. Execute:
   ```powershell
   cursor --disable-extensions
   ```
4. Teste se Ctrl+C/V funciona sem extensões

---

## Se NADA funcionar:

### Verificar configuração do Windows

1. Pressione `Win + I` (Configurações)
2. Vá em: **Acessibilidade** → **Teclado**
3. Verifique se **"Teclas de Aderência"** está **DESATIVADA**
4. Verifique se **"Teclas de Filtro"** está **DESATIVADA**

### Testar com outro usuário Windows

1. Crie um usuário temporário do Windows
2. Logue com esse usuário
3. Teste Ctrl+C/V
4. Se funcionar = problema nas configurações do seu usuário atual

---

## Última solução (extrema):

Se NADA resolver, pode ser:
- Driver de teclado corrompido
- Software de terceiros interceptando atalhos (AutoHotkey, etc)
- Problema de hardware do teclado

**Teste com outro teclado** (USB ou Bluetooth) para descartar hardware.

