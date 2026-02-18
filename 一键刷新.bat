@echo off
chcp 65001 >nul
title 项目批处理程序（从注册表查找Python 3.11）

REM 从注册表查找Python 3.11安装路径
set "PYTHON_PATH="

REM 查找Python 3.11的核心版本
for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.11\InstallPath" /v ExecutablePath 2^>nul') do (
    set "PYTHON_PATH=%%B"
)

REM 如果没找到，尝试32位注册表
if "%PYTHON_PATH%"=="" (
    for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\WOW6432Node\Python\PythonCore\3.11\InstallPath" /v ExecutablePath 2^>nul') do (
        set "PYTHON_PATH=%%B"
    )
)

REM 如果仍然没找到，尝试查找用户安装的版本
if "%PYTHON_PATH%"=="" (
    for /f "tokens=2*" %%A in ('reg query "HKCU\SOFTWARE\Python\PythonCore\3.11\InstallPath" /v ExecutablePath 2^>nul') do (
        set "PYTHON_PATH=%%B"
    )
)

REM 最终检查
if "%PYTHON_PATH%"=="" (
    echo 错误：未在注册表中找到Python 3.11
    echo 请确保已安装Python 3.11
    pause
    exit /b 1
)

echo 从注册表找到Python 3.11路径: %PYTHON_PATH%

REM 验证文件是否存在
if not exist "%PYTHON_PATH%" (
    echo 错误：Python可执行文件不存在: %PYTHON_PATH%
    pause
    exit /b 1
)

REM 这里可以继续您的其他代码
echo 运行Python程序...

REM 检查Python路径是否存在
if not exist "%PYTHON_PATH%" (
    echo 错误: Python 3.11未找到在 %PYTHON_PATH%
    echo 请修改PYTHON_PATH变量为您的Python 3.11实际安装路径
    pause
    exit /b 1
)

echo Python 3.11路径: %PYTHON_PATH%

REM 获取当前批处理文件所在的目录作为根目录
set "ROOT_DIR=%~dp0"

REM 去掉路径末尾的反斜杠
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

echo 项目批处理程序开始执行...
echo 当前工作目录: %ROOT_DIR%
echo 使用的Python版本: 3.11
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
    "%PYTHON_PATH%" "转换TXT到CSV相对路径.py"
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
    "%PYTHON_PATH%" "Csv_true.py"
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
    "%PYTHON_PATH%" "Csv_All.py"
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
