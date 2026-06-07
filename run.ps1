# bilibili-sub-md 启动脚本
# 运行时会提示输入 SESSDATA，输入一次后当前窗口内有效

$pythonPath = "C:/Users/15403/AppData/Local/Programs/Python/Python311/python.exe"
$scriptPath = "e:/git项目/Codex/bilibili-sub-md/main.py"

# 检查是否已经设置了 BILI_COOKIE
if (-not $env:BILI_COOKIE) {
    Write-Host "请输入你的 Bilibili SESSDATA（从浏览器 Cookie 中复制，粘贴后按回车）：" -ForegroundColor Cyan
    $sessdata = Read-Host
    if ($sessdata) {
        $env:BILI_COOKIE = $sessdata
        Write-Host "已设置 Cookie" -ForegroundColor Green
    } else {
        Write-Host "未提供 Cookie，将以游客身份运行（部分字幕可能无法获取）" -ForegroundColor Yellow
    }
} else {
    Write-Host "检测到已设置 BILI_COOKIE 环境变量" -ForegroundColor Green
}

& $pythonPath $scriptPath

Write-Host "`n按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
