# Script para resetar clipboard rapidamente
# Uso: .\reset-clipboard.ps1

Write-Host "[INICIO] Resetando clipboard..." -ForegroundColor Cyan

# 1. Limpar clipboard via .NET
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Clipboard]::Clear()
Start-Sleep -Milliseconds 500

# 2. Resetar via Win32 API
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$cbdll = Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern bool OpenClipboard(IntPtr hWndNewOwner); [DllImport("user32.dll")] public static extern bool EmptyClipboard(); [DllImport("user32.dll")] public static extern bool CloseClipboard();' -Name "Clipboard$timestamp" -Namespace "Win32API$timestamp" -PassThru
$cbdll::OpenClipboard([IntPtr]::Zero)
$cbdll::EmptyClipboard()
$cbdll::CloseClipboard()

# 3. Reiniciar processo rdpclip
Stop-Process -Name "rdpclip" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 4. Teste
[System.Windows.Forms.Clipboard]::SetText("TESTE_OK")
$result = [System.Windows.Forms.Clipboard]::GetText()
[System.Windows.Forms.Clipboard]::Clear()

if($result -eq "TESTE_OK") {
    Write-Host "[OK] Clipboard resetado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "[WARN] Possível problema - tente novamente" -ForegroundColor Yellow
}

Write-Host "[FIM] Pronto para copiar/colar!" -ForegroundColor Cyan
