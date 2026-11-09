@echo off
chcp 65001 >nul
echo ========================================================
echo       正在将 Bokeman 工作流切换为新版 (v2 自然连接工作流)...
echo ========================================================

copy /y backup\workflow-v2\js\*.js js\ >nul
copy /y backup\workflow-v2\skills\SKILL.md .agents\skills\oogiri-flow\SKILL.md >nul
copy /y backup\workflow-v2\bench\PROMPTS_FINGERPRINT bench\ab-divergence\PROMPTS_FINGERPRINT >nul

echo 正在校验新版提示词指纹...
python bench\ab-divergence\prompts.py --check

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo  [成功] 已无缝切换至新版工作流 (v2)！
    echo  您只需刷新浏览器即可直接使用新版大喜利工作流。
    echo ========================================================
) else (
    echo.
    echo  [警告] 指纹对账异常，请检查文件完整性。
)
pause
