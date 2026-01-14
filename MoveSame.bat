@echo off
setlocal enabledelayedexpansion

REM 设置路径变量
set "CSV_DIR=Exported_Labels_csv"
set "SOURCE_DIR=Images_To_Sort"
set "DEST_DIR=Sorted_Images"

REM 检查必要目录是否存在
if not exist "%CSV_DIR%" (
    echo Error: Directory %CSV_DIR% does not exist!
    pause
    exit /b 1
)

if not exist "%SOURCE_DIR%" (
    echo Error: Directory %SOURCE_DIR% does not exist!
    pause
    exit /b 1
)

REM 创建目标目录（如果不存在）
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
)

REM 查找所有CSV文件
set "csv_count=0"
for %%i in ("%CSV_DIR%\*.csv") do (
    set /a "csv_count+=1"
    set "csv_file=%%~nxi"
    echo Processing CSV file: !csv_file!
    
    REM 读取CSV文件并移动图片
    set "moved_count=0"
    set "skipped_count=0"
    
    for /f "usebackq tokens=1,* delims=," %%a in ("%CSV_DIR%\!csv_file!") do (
        REM 跳过第一行（标题行）
        if /i not "%%a"=="图片路径" (
            set "image_path=%%a"
            
            REM 移除路径中的引号（如果有）
            set "image_path=!image_path:"=!"
            
            REM 提取文件名
            for %%f in ("!image_path!") do set "filename=%%~nxf"
            
            REM 检查源文件是否存在
            if exist "!image_path!" (
                echo Moving: !filename!
                move "!image_path!" "%DEST_DIR%\" >nul
                set /a "moved_count+=1"
            ) else (
                echo Skipping: !filename! (not found in %SOURCE_DIR%)
                set /a "skipped_count+=1"
            )
        )
    )
    
    echo Processed !csv_file! - Images moved: !moved_count!, skipped: !skipped_count!
    echo.
)

if !csv_count! equ 0 (
    echo No CSV files found in %CSV_DIR%!
    pause
    exit /b 1
)

echo All operations completed!
echo Total CSV files processed: %csv_count%
echo.