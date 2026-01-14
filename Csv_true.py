import os
import pandas as pd
import glob
import re
from pathlib import Path

def find_latest_csv_file(csv_folder):
    """
    在指定文件夹中查找最新的CSV文件
    """
    # 使用glob查找所有CSV文件
    csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"在文件夹 {csv_folder} 中未找到CSV文件")
    
    # 按修改时间排序，获取最新的文件
    latest_csv = max(csv_files, key=os.path.getmtime)
    return latest_csv

def process_image_paths(df):
    """
    处理DataFrame中的图片路径，将Images_To_Sort替换为Sorted_Images
    """
    # 复制DataFrame以避免修改原始数据
    processed_df = df.copy()
    
    # 遍历所有列，查找包含图片路径的列
    for col in processed_df.columns:
        # 检查列中是否包含图片路径（包含Images_To_Sort）
        if processed_df[col].astype(str).str.contains('Images_To_Sort', na=False).any():
            # 替换路径
            processed_df[col] = processed_df[col].astype(str).str.replace(
                'Images_To_Sort', 'Sorted_Images', regex=False
            )
    
    return processed_df

def main():
    # 定义文件夹路径
    script_dir = os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录（项目根目录）
    input_folder = os.path.join(script_dir, "Exported_Labels_csv")
    output_folder = os.path.join(script_dir, "Exported_Labels_csv_true")
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        # 查找最新的CSV文件
        latest_csv = find_latest_csv_file(input_folder)
        print(f"找到最新CSV文件: {os.path.basename(latest_csv)}")
        
        # 读取CSV文件，处理可能的编码问题
        try:
            # 尝试UTF-8编码
            df = pd.read_csv(latest_csv, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # 尝试GBK编码（中文）
                df = pd.read_csv(latest_csv, encoding='gbk')
            except UnicodeDecodeError:
                # 尝试其他常见编码
                df = pd.read_csv(latest_csv, encoding='latin-1')
        
        print(f"成功读取CSV文件，共 {len(df)} 行数据")
        
        # 处理图片路径
        processed_df = process_image_paths(df)
        
        # 生成输出文件名（添加"_true"后缀）
        input_filename = Path(latest_csv).stem  # 获取文件名（不含扩展名）
        output_filename = f"{input_filename}_true.csv"
        output_path = os.path.join(output_folder, output_filename)
        
        # 保存处理后的数据（使用UTF-8编码避免中文问题）
        processed_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"处理完成！输出文件已保存至: {output_path}")
        print(f"原文件: {latest_csv}")
        print(f"新文件: {output_path}")
        
        # 显示一些处理前后的路径对比示例
        print("\n路径替换示例:")
        for col in df.columns:
            if df[col].astype(str).str.contains('Images_To_Sort', na=False).any():
                # 找到包含Images_To_Sort的行
                old_paths = df[col].dropna().astype(str)
                new_paths = processed_df[col].dropna().astype(str)
                
                # 显示前3个示例
                for i, (old, new) in enumerate(zip(old_paths.head(3), new_paths.head(3))):
                    if 'Images_To_Sort' in old:
                        print(f"  {old} -> {new}")
                        if i >= 2:  # 只显示3个示例
                            break
                break
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")

if __name__ == "__main__":
    main()
