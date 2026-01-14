@echo off
chcp 65001 >nul
title 项目批处理程序

REM 获取当前批处理文件所在的目录作为根目录
set "ROOT_DIR=%~dp0"

REM 去掉路径末尾的反斜杠
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

echo 项目批处理程序开始执行...
echo 当前工作目录: %ROOT_DIR%
echo ========================================

REM 1. 执行 MoveSame.bat
echo [1/6] 正在执行 MoveSame.bat...
if exist "%ROOT_DIR%\MoveSame.bat" (
    cd /d "%ROOT_DIR%"
    call "MoveSame.bat"
    if errorlevel 1 (
        echo 错误: MoveSame.bat 执行失败！
        pause
    )
    echo MoveSame.bat 执行完成！
) else (
    echo 警告: MoveSame.bat 文件不存在，跳过...
)
echo.

REM 2. 执行 batch_process.bat
echo [2/6] 正在执行 batch_process.bat...
if exist "%ROOT_DIR%\batch_process.bat" (
    cd /d "%ROOT_DIR%"
    call "batch_process.bat"
    )
    echo batch_process.bat 执行完成！
) else (
    echo 警告: batch_process.bat 文件不存在，跳过...
)
echo.

REM 3. 执行 转换TXT到CSV相对路径.py
echo [3/6] 正在执行 转换TXT到CSV相对路径.py...
if exist "%ROOT_DIR%\转换TXT到CSV相对路径.py" (
    cd /d "%ROOT_DIR%"
    python "转换TXT到CSV相对路径.py"
    if errorlevel 1 (
        echo 错误: 转换TXT到CSV相对路径.py 执行失败！
        pause
        exit /b 1
    )
    echo 转换TXT到CSV相对路径.py 执行完成！
) else (
    echo 警告: 转换TXT到CSV相对路径.py 文件不存在，跳过...
)
echo.

REM 4. 执行 Csv_true.py
echo [4/6] 正在执行 Csv_true.py...
if exist "%ROOT_DIR%\Csv_true.py" (
    cd /d "%ROOT_DIR%"
    python "Csv_true.py"
    if errorlevel 1 (
        echo 错误: Csv_true.py 执行失败！
        pause
        exit /b 1
    )
    echo Csv_true.py 执行完成！
) else (
    echo 警告: Csv_true.py 文件不存在，跳过...
)
echo.

REM 5. 执行 Csv_All.py
echo [5/6] 正在执行 Csv_All.py...
if exist "%ROOT_DIR%\Csv_All.py" (
    cd /d "%ROOT_DIR%"
    python "Csv_All.py"
    if errorlevel 1 (
        echo 错误: Csv_All.py 执行失败！
        pause
        exit /b 1
    )
    echo Csv_All.py 执行完成！
) else (
    echo 警告: Csv_All.py 文件不存在，跳过...
)
echo.

REM 6. 再次执行 MoveSame.bat
echo [6/6] 正在执行 MoveSame.bat...
if exist "%ROOT_DIR%\MoveSame.bat" (
    cd /d "%ROOT_DIR%"
    call "MoveSame.bat"
    if errorlevel 1 (
        echo 错误: MoveSame.bat 执行失败！
        pause
        exit /b 1
    )
    echo MoveSame.bat 执行完成！
) else (
    echo 警告: MoveSame.bat 文件不存在，跳过...
)
echo.

echo ========================================
echo 所有程序已按顺序执行完成！
echo.
pause