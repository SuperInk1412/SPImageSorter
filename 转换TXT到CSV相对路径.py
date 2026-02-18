#!/usr/bin/env python3.11
import re
import pandas as pd
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import glob
import chardet  # 新增：用于检测文件编码


def detect_file_encoding(file_path):
    """
    自动检测文件编码，解决UnicodeDecodeError问题
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            print(f"📝 自动检测文件编码: {encoding} (可信度: {confidence:.2f})")
            return encoding
    except Exception as e:
        print(f"⚠️  编码检测失败，使用默认编码 GBK: {e}")
        return 'gbk'


def convert_deepdanbooru_txt_to_csv(txt_file_path, csv_file_path=None, relative_to=None):
    """
    将DeepDanbooru输出的TXT文件转换为CSV格式
    relative_to: 相对路径的基准目录，如果为None则使用txt文件所在目录
    """
    
    if csv_file_path is None:
        txt_path = Path(txt_file_path)
        csv_file_path = txt_path.parent / f"{txt_path.stem}_CSV格式.csv"
    
    print(f"正在转换: {txt_file_path}")
    
    # 设置相对路径基准目录
    if relative_to is None:
        relative_to = Path(txt_file_path).parent
    else:
        relative_to = Path(relative_to)
    
    # ========== 核心修改：自动检测编码并读取文件 ==========
    # 检测文件编码
    file_encoding = detect_file_encoding(txt_file_path)
    # 尝试使用检测到的编码读取，失败则依次尝试常用编码
    encodings_to_try = [file_encoding, 'gbk', 'gb2312', 'utf-8', 'gb18030']
    lines = None
    
    for enc in encodings_to_try:
        try:
            with open(txt_file_path, 'r', encoding=enc, errors='ignore') as f:
                lines = f.readlines()
            print(f"✅ 使用编码 {enc} 成功读取文件")
            break
        except Exception as e:
            print(f"⚠️  使用编码 {enc} 读取失败: {e}")
            continue
    
    if lines is None:
        print("❌❌❌❌ 所有编码尝试均失败，无法读取文件")
        return None
    # ========== 编码读取部分修改结束 ==========
    
    results = []
    current_image = None
    current_tags = []
    current_confidences = []
    
    tag_pattern = re.compile(r'^\(([0-9.]+)\)\s+(.+)$')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # 检查是否是新的图片开始
        if line.startswith('Tags of '):
            # 保存上一个图片的数据
            if current_image is not None and current_tags:
                # 转换为相对路径
                abs_image_path = Path(current_image)
                try:
                    relative_image_path = abs_image_path.relative_to(relative_to)
                except ValueError:
                    # 如果路径不在基准目录下，使用绝对路径
                    relative_image_path = abs_image_path
                
                results.append({
                    '图片路径': str(relative_image_path),
                    '标签数量': len(current_tags),
                    '标签': ', '.join(current_tags),
                    '标签(带置信度)': ', '.join([f'{tag} ({conf})' for tag, conf in zip(current_tags, current_confidences)]),
                    '置信度列表': ', '.join([f'{conf:.3f}' for conf in current_confidences])
                })
            
            # 移除 "Tags of " 和末尾的冒号
            image_path = line.replace('Tags of ', '')
            if image_path.endswith(':'):
                image_path = image_path[:-1]
            
            current_image = image_path.strip()
            current_tags = []
            current_confidences = []
        
        # 检查是否是标签行
        elif line.startswith('('):
            match = tag_pattern.match(line)
            if match:
                confidence = float(match.group(1))
                tag = match.group(2).strip()
                current_tags.append(tag)
                current_confidences.append(confidence)
    
    # 保存最后一个图片的数据
    if current_image is not None and current_tags:
        # 转换为相对路径（修复原代码的变量名错误：relative_base → relative_to）
        abs_image_path = Path(current_image)
        try:
            relative_image_path = abs_image_path.relative_to(relative_to)
        except ValueError:
            # 如果路径不在基准目录下，使用绝对路径
            relative_image_path = abs_image_path
        
        results.append({
            '图片路径': str(relative_image_path),
            '标签数量': len(current_tags),
            '标签': ', '.join(current_tags),
            '标签(带置信度)': ', '.join([f'{tag} ({conf})' for tag, conf in zip(current_tags, current_confidences)]),
            '置信度列表': ', '.join([f'{conf:.3f}' for conf in current_confidences])
        })
    
    if results:
        df = pd.DataFrame(results)
        
        # 按标签数量排序
        df = df.sort_values('标签数量', ascending=False).reset_index(drop=True)
        
        # 保存为CSV
        df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ 转换完成！")
        print(f"   处理的图片数量: {len(results)}")
        print(f"   输出文件: {csv_file_path}")
        print(f"   相对路径基准目录: {relative_to}")
        
        # 验证路径格式
        print("\n📁📁📁📁 验证前3条路径格式:")
        for i in range(min(3, len(df))):
            path = df.iloc[i]['图片路径']
            print(f"  {i+1}. {path}")
        
        return csv_file_path
    else:
        print("❌❌❌❌ 没有找到有效的图片数据")
        return None


def check_pandas_installed():
    """检查pandas是否已安装"""
    try:
        import pandas
        return True
    except ImportError:
        return False


def find_latest_txt_file(directory):
    """
    在指定目录下查找最新的TXT文件
    文件名格式示例：图片标签数据_20260112_021529.txt
    """
    # 匹配文件名模式：图片标签数据_YYYYMMDD_HHMMSS.txt
    pattern = os.path.join(directory, "图片标签数据_*.txt")
    txt_files = glob.glob(pattern)
    
    if not txt_files:
        # 如果没有找到特定格式的文件，查找所有TXT文件
        txt_files = glob.glob(os.path.join(directory, "*.txt"))
    
    if not txt_files:
        return None
    
    # 按修改时间排序，获取最新的文件
    latest_file = max(txt_files, key=os.path.getmtime)
    return latest_file


# =============================
# ===== 主程序开始 ============
# =============================

if __name__ == "__main__":
    print("=" * 60)
    print("DeepDanbooru TXT转CSV工具 (自动选择最新文件版)")
    print("=" * 60)

    # ===== 检查依赖 =====
    required_packages = {'pandas': check_pandas_installed()}
    try:
        import chardet
        required_packages['chardet'] = True
    except ImportError:
        required_packages['chardet'] = False

    # 检查缺失的依赖
    missing_packages = [pkg for pkg, installed in required_packages.items() if not installed]
    if missing_packages:
        print("❌❌❌❌ 错误: 缺少必要的模块")
        for pkg in missing_packages:
            print(f"   - {pkg} 未安装")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        input("\n按Enter键退出...")
        exit(1)

    # ===== 自动查找最新文件 =====
    script_dir = os.path.dirname(os.path.abspath(__file__))
    exported_labels_dir = os.path.join(script_dir, "Exported_Labels")
    exported_labels_dir = os.path.normpath(exported_labels_dir)

    print(f"📂📂📂📂 正在查找 Exported_Labels 文件夹: {exported_labels_dir}")
    
    # 检查目录是否存在
    if not os.path.exists(exported_labels_dir):
        print(f"❌❌❌❌ 错误: Exported_Labels 文件夹不存在")
        print(f"请确保在脚本同目录下存在 Exported_Labels 文件夹")
        input("\n按 Enter 键退出...")
        exit()

    # 查找最新文件
    latest_txt_file = find_latest_txt_file(exported_labels_dir)
    
    if not latest_txt_file:
        print("❌❌❌❌ 错误: 在 Exported_Labels 文件夹中未找到任何TXT文件")
        input("\n按 Enter 键退出...")
        exit()

    print(f"✅ 找到最新文件: {latest_txt_file}")
    print(f"   文件修改时间: {os.path.getmtime(latest_txt_file)}")
    
    txt_files = [latest_txt_file]

    # ===== 自动选择模式1 =====
    print("\n📁📁 自动选择模式1: 使用脚本所在目录作为基准目录")
    relative_base = Path(script_dir)
    print(f"   基准目录: {relative_base}")

    # ===== 设置 CSV 输出目录 =====
    output_csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Exported_Labels_csv")
    os.makedirs(output_csv_dir, exist_ok=True)
    print(f"📂📂📂📂 CSV 文件将保存到: {output_csv_dir}")

    # ===== 开始转换文件 =====
    for txt_file_path in txt_files:
        print(f"\n🔍🔍🔍🔍 正在处理文件: {txt_file_path}")

        # 构造输出 CSV 文件路径
        txt_path_obj = Path(txt_file_path)
        csv_filename = f"{txt_path_obj.stem}_CSV格式.csv"
        csv_file_path = os.path.join(output_csv_dir, csv_filename)

        # 调用转换函数
        result_csv_path = convert_deepdanbooru_txt_to_csv(
            txt_file_path, 
            csv_file_path=csv_file_path,
            relative_to=relative_base
        )

        if result_csv_path:
            print(f"✅ 转换成功！CSV 已保存至: {result_csv_path}")
        else:
            print(f"❌❌❌❌ 转换失败或无有效数据: {txt_file_path}")

    print("\n" + "="*60)
    print("🎉🎉🎉🎉 文件处理完成！")
    print(f"📁📁📁📁 CSV 文件保存在: {output_csv_dir}")
    print(f"📁📁 相对路径基准目录: {relative_base}")
