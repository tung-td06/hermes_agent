# Force CocCoc windows to restore + foreground so the user can see them
$ErrorActionPreference = 'SilentlyContinue'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
}
'@
$ws = New-Object -ComObject WScript.Shell
$wins = Get-Process browser -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
foreach ($w in $wins) {
    Write-Output ("WIN id={0} title={1}" -f $w.Id, $w.MainWindowTitle)
    [Win32]::ShowWindow($w.MainWindowHandle, 9) | Out-Null   # SW_RESTORE
    $null = $ws.AppActivate($w.Id)
    Start-Sleep -Milliseconds 400
    [Win32]::SetForegroundWindow($w.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 400
}
Write-Output "DONE"
