@echo off
chcp 65001 >nul
cls
echo ========================================
echo  DeepDanbooru 动漫图片批量标签化工具
echo ========================================
echo.
REM 设置文件输出路径
set "OUTPUT_DIR=Exported_Labels"
set "MODEL_PATH=Model_Files\deepdanbooru-v3-20211112-sgd-e28"
set "IMAGE_PATH=Images_To_Sort"

REM 获取当前日期时间，并定义输出文件名称
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "datetime=%%a"
set "HHMMSS=%datetime:~8,6%"
set "YYYYMMDD=%datetime:~0,8%"
set "TIMESTAMP=%YYYYMMDD%_%HHMMSS%"
set "OUTPUT_FILE=%OUTPUT_DIR%\图片标签数据_%TIMESTAMP%.txt"

echo ⏳ 正在加载模型，请稍候...
echo   这将需要一些时间，请耐心等待...
echo.

echo 正在处理图片并生成标签数据...
echo.

REM 使用重定向将输出保存到文件
deepdanbooru evaluate "%IMAGE_PATH%" --project-path "%MODEL_PATH%" --allow-folder --threshold 0.5 > "%OUTPUT_FILE%"

echo.
echo ========================================
echo  文件生成完成！
echo ========================================
echo.

REM 获取当前目录的绝对路径 - 使用更简单的方法
set "CURRENT_DIR=%CD%\"
set "FULL_PATH=%CURRENT_DIR%%OUTPUT_FILE%"

REM 将反斜杠替换为正斜杠避免编码问题
set "DISPLAY_PATH=%FULL_PATH:\=/%"

echo 生成的标签文件路径为：
echo %DISPLAY_PATH%
echo.

REM 同时显示Windows格式的路径（备用）
echo Windows格式路径：
echo %FULL_PATH%
echo.

REM 检查文件是否存在
if exist "%OUTPUT_FILE%" (
    echo ✅ 文件已成功生成并保存
) else (
    echo ❌ 警告：文件可能未正确生成
)

echo.
echo 按任意键退出程序...