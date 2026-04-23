@echo off
echo 网络修复脚本 - 清理代理和DNS缓存
echo =================================
echo.

echo [1] 检查网络适配器
ipconfig /all | findstr /i "IPv4 Default Gateway DNS"

echo.
echo [2] 清理 DNS 缓存
ipconfig /flushdns
echo DNS缓存已清理。

echo.
echo [3] 重置 Winsock
netsh winsock reset
echo Winsock 已重置（需要重启生效）。

echo.
echo [4] 设置代理状态（当前）
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer

echo.
echo [5] 开启代理（fxy模式）
echo reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f
echo reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:7890" /f
echo.

echo [6] 关闭代理（正常模式）
echo reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f
echo.

echo [7] 检查网络连通性
ping -n 2 8.8.8.8 >nul && (
  echo √ 网络连接正常
) || (
  echo × 网络连接失败
)

echo.
echo 脚本执行完成。
echo 如果问题依旧，建议：
echo 1. 重启电脑
echo 2. 检查防火墙设置
echo 3. 禁用 VPN 适配器（设备管理器 -> 网络适配器 -> TAP-Windows Adapter V9）
pause