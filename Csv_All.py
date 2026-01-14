import os
import pandas as pd
import glob
from datetime import datetime
import hashlib

def get_latest_csv(folder_path):
    """获取指定文件夹中最新的CSV文件"""
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not csv_files:
        return None
    # 按修改时间排序获取最新文件
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file

def align_columns(df_target, df_source):
    """
    对齐列结构，确保两个DataFrame有相同的列
    优先保留目标DataFrame的列结构
    """
    # 获取目标DataFrame的列
    target_columns = df_target.columns.tolist()
    source_columns = df_source.columns.tolist()
    
    print(f"目标文件列数: {len(target_columns)}")
    print(f"源文件列数: {len(source_columns)}")
    print(f"目标文件列名: {target_columns}")
    print(f"源文件列名: {source_columns}")
    
    # 找出缺失的列
    missing_columns = [col for col in target_columns if col not in source_columns]
    extra_columns = [col for col in source_columns if col not in target_columns]
    
    if missing_columns:
        print(f"源文件缺少列: {missing_columns}")
    if extra_columns:
        print(f"源文件多余列: {extra_columns}")
    
    # 添加缺失的列并填充空值
    for col in missing_columns:
        df_source[col] = ""
        print(f"已添加缺失列: {col}")
    
    # 删除多余的列
    columns_to_drop = [col for col in extra_columns if col not in target_columns]
    if columns_to_drop:
        df_source = df_source.drop(columns=columns_to_drop)
        print(f"已删除多余列: {columns_to_drop}")
    
    # 重新排列列顺序以匹配目标DataFrame
    df_source = df_source.reindex(columns=target_columns)
    
    return df_source

def merge_latest_csv_files():
    """
    合并Csv_All文件夹内最新的一个csv文件与Exported_Labels_csv_true文件夹内最新的一个csv文件
    处理列结构不匹配问题，优先保留绝对路径
    """
    input_folder = "Exported_Labels_csv_true"
    output_folder = "Csv_All"
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 获取两个文件夹中最新的CSV文件
    latest_input = get_latest_csv(input_folder)
    latest_output = get_latest_csv(output_folder)
    
    if not latest_input:
        print(f"在文件夹 {input_folder} 中未找到CSV文件")
        return
    
    all_data = []
    target_columns = None
    
    # 读取两个最新的CSV文件
    files_to_read = []
    if latest_input:
        files_to_read.append(('input', latest_input))
    if latest_output:
        files_to_read.append(('output', latest_output))
    
    print(f"将合并以下文件: {[f[1] for f in files_to_read]}")
    
    for file_type, file_path in files_to_read:
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"成功读取文件 {os.path.basename(file_path)}，编码: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"使用编码 {encoding} 读取文件 {file_path} 时出错: {e}")
                    continue
            
            if df is None:
                print(f"无法读取文件 {file_path}，跳过")
                continue
            
            # 添加源文件列
            df['source_file'] = os.path.basename(file_path)
            
            # 设置目标列结构（以第一个文件的列结构为准）
            if target_columns is None:
                target_columns = df.columns.tolist()
                all_data.append(df)
                print(f"设置目标列结构: {target_columns}")
            else:
                # 对齐列结构
                print(f"对齐文件 {os.path.basename(file_path)} 的列结构...")
                df_aligned = align_columns(all_data[0], df)
                all_data.append(df_aligned)
                print(f"文件 {os.path.basename(file_path)} 列结构对齐完成")
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            continue
    
    if not all_data:
        print("没有成功读取任何CSV文件")
        return
    
    try:
        merged_df = pd.concat(all_data, ignore_index=True)
        print(f"合并后总行数: {len(merged_df)}")
        
        # 去重处理 - 优先保留绝对路径
        def create_hash(row):
            # 使用图片路径作为主要去重依据，确保绝对路径优先
            content = str(row['图片路径'])
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        
        merged_df['content_hash'] = merged_df.apply(create_hash, axis=1)
        
        initial_count = len(merged_df)
        # 优先保留较新的记录（假设后面的文件较新）
        merged_df = merged_df.drop_duplicates(subset=['content_hash'], keep='last')
        final_count = len(merged_df)
        
        print(f"去除重复项: {initial_count} -> {final_count} (去除 {initial_count - final_count} 个重复项)")
        
        merged_df = merged_df.drop('content_hash', axis=1)
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_filename = f"所有图片标签_{timestamp}.csv"
        output_path = os.path.join(output_folder, output_filename)
        
        merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"成功保存合并文件: {output_path}")
        print(f"最终数据行数: {len(merged_df)}")
        print(f"列数: {len(merged_df.columns)}")
        print("列名:", merged_df.columns.tolist())
        
        if 'source_file' in merged_df.columns:
            file_counts = merged_df['source_file'].value_counts()
            print("\n各源文件贡献的行数:")
            for file, count in file_counts.items():
                print(f"  {file}: {count} 行")
                
    except Exception as e:
        print(f"处理数据时出错: {e}")
        try:
            # 备用保存方案
            merged_df.to_csv(output_path, index=False, encoding='gbk')
            print(f"使用GBK编码成功保存文件: {output_path}")
        except Exception as e2:
            print(f"使用GBK编码保存也失败: {e2}")

def main():
    print("开始合并最新的CSV文件（处理列结构不匹配）...")
    print("=" * 50)
    merge_latest_csv_files()
    print("=" * 50)
    print("处理完成！")

if __name__ == "__main__":
    main()
