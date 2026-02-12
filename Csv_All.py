import os
import pandas as pd
import glob
from datetime import datetime
import hashlib
from pathlib import Path

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

def get_image_file_modification_date(image_path, base_path=""):
    """获取图片文件的修改日期（Windows系统）"""
    try:
        # 处理图片路径
        # 根据文档内容，图片路径可能是相对路径
        full_path = image_path
        
        # 如果提供基础路径，尝试构建完整路径
        if base_path and not os.path.isabs(image_path):
            # 尝试几种可能的路径组合
            possible_paths = [
                os.path.join(base_path, image_path),
                os.path.join(os.path.dirname(base_path), image_path),
                image_path  # 原始路径
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    full_path = path
                    break
        
        # 使用pathlib获取文件信息
        file_path_obj = Path(full_path)
        if file_path_obj.exists():
            # 获取文件的修改时间（Windows系统）
            mod_time = file_path_obj.stat().st_mtime
            # 转换为可读的日期时间格式
            return datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        else:
            # 文件不存在，返回空字符串
            print(f"警告：图片文件不存在: {full_path}")
            return ""
            
    except Exception as e:
        print(f"获取图片文件 {image_path} 修改日期时出错: {e}")
        return ""

def add_image_modification_dates(df, csv_file_path):
    """
    为DataFrame添加图片文件的修改日期
    读取第一列（图片路径）中每个图片文件的修改日期
    """
    # 确定第一列的列名（从文档看是"图片路径"）
    image_path_column = None
    possible_names = ["图片路径", "图片路径", "图片", "路径", "image_path", "path"]
    
    for col in df.columns:
        if col in possible_names:
            image_path_column = col
            break
    
    if not image_path_column:
        # 如果没有找到标准列名，使用第一列
        image_path_column = df.columns[0]
        print(f"未找到标准图片路径列名，使用第一列: {image_path_column}")
    
    print(f"使用列 '{image_path_column}' 作为图片路径")
    
    # 获取CSV文件所在目录，用于解析相对路径
    csv_dir = os.path.dirname(csv_file_path) if csv_file_path else ""
    
    # 创建空列表存储修改日期
    modification_dates = []
    
    # 遍历每行的图片路径
    for index, row in df.iterrows():
        image_path = str(row[image_path_column]) if pd.notna(row[image_path_column]) else ""
        
        if image_path:
            # 获取图片文件的修改日期
            mod_date = get_image_file_modification_date(image_path, csv_dir)
            modification_dates.append(mod_date)
        else:
            # 图片路径为空，添加空字符串
            modification_dates.append("")
    
    # 在G列位置（第7列，索引6）插入修改日期
    insert_position = min(6, len(df.columns))  # 确保位置有效
    
    if "图片修改日期" not in df.columns:
        # 插入新列
        df.insert(insert_position, "图片修改日期", modification_dates)
        print(f"已在第{insert_position+1}列添加'图片修改日期'列")
    else:
        # 更新现有列
        df["图片修改日期"] = modification_dates
        print(f"已更新'图片修改日期'列")
    
    # 统计成功获取日期的文件数量
    valid_dates = [d for d in modification_dates if d]
    print(f"成功获取 {len(valid_dates)}/{len(modification_dates)} 个图片文件的修改日期")
    
    return df

def merge_latest_csv_files():
    """
    合并Csv_All文件夹内最新的一个csv文件与Exported_Labels_csv_true文件夹内最新的一个csv文件
    处理列结构不匹配问题，优先保留绝对路径，并添加图片文件修改日期到G列
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
            
            # 为每个图片文件添加修改日期
            df = add_image_modification_dates(df, file_path)
            
            # 设置目标列结构（以第一个文件的列结构为准）
            if target_columns is None:
                # 更新目标列结构
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
            import traceback
            traceback.print_exc()
            continue
    
    if not all_data:
        print("没有成功读取任何CSV文件")
        return
    
    try:
        if len(all_data) > 1:
            merged_df = pd.concat(all_data, ignore_index=True)
        else:
            merged_df = all_data[0]
            
        print(f"合并后总行数: {len(merged_df)}")
        
        # 去重处理 - 优先保留绝对路径
        def create_hash(row):
            # 使用图片路径作为主要去重依据，确保绝对路径优先
            content = str(row['图片路径']) if '图片路径' in row else ""
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # 确保去重时包含所有必要的列
        merged_df['content_hash'] = merged_df.apply(create_hash, axis=1)
        
        initial_count = len(merged_df)
        
        # 检查是否真的有重复项
        duplicate_mask = merged_df.duplicated(subset=['content_hash'], keep='last')
        duplicates_count = duplicate_mask.sum()
        
        if duplicates_count > 0:
            print(f"找到 {duplicates_count} 个重复项")
            # 优先保留较新的记录（假设后面的文件较新）
            merged_df = merged_df.drop_duplicates(subset=['content_hash'], keep='last')
        else:
            print("未找到重复项")
            
        final_count = len(merged_df)
        
        if initial_count != final_count:
            print(f"去除重复项: {initial_count} -> {final_count} (去除 {initial_count - final_count} 个重复项)")
        
        # 移除临时列
        if 'content_hash' in merged_df.columns:
            merged_df = merged_df.drop('content_hash', axis=1)
        
        # 最终确保'图片修改日期'列在G列位置（第7列，索引6）
        if '图片修改日期' in merged_df.columns:
            current_columns = merged_df.columns.tolist()
            
            # 确定期望的列顺序：图片路径、标签数量、标签、标签(带置信度)、置信度列表、source_file、图片修改日期
            # 查找图片修改日期列的当前位置
            current_idx = current_columns.index('图片修改日期')
            expected_position = 6  # G列位置
            
            if current_idx != expected_position and len(current_columns) > expected_position:
                try:
                    # 重新排序列
                    cols_to_move = ['图片修改日期']
                    other_cols = [col for col in current_columns if col not in cols_to_move]
                    
                    # 确保source_file在图片修改日期之前
                    # 如果source_file在图片修改日期之后，需要调整
                    if 'source_file' in other_cols and other_cols.index('source_file') >= expected_position:
                        # 将source_file也移到正确位置
                        source_file_idx = other_cols.index('source_file')
                        other_cols.pop(source_file_idx)
                        # 插入到图片修改日期之前
                        other_cols.insert(expected_position - 1, 'source_file')
                    
                    # 插入图片修改日期到G列
                    new_columns = other_cols[:expected_position] + cols_to_move + other_cols[expected_position:]
                    merged_df = merged_df[new_columns]
                    
                    print(f"已确认'图片修改日期'列在第{expected_position+1}列（G列）")
                    
                except Exception as e:
                    print(f"调整列顺序时出错: {e}")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_filename = f"所有图片标签_{timestamp}.csv"
        output_path = os.path.join(output_folder, output_filename)
        
        merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"成功保存合并文件: {output_path}")
        print(f"最终数据行数: {len(merged_df)}")
        print(f"列数: {len(merged_df.columns)}")
        print("列名:", merged_df.columns.tolist())
        
        # 显示图片修改日期的统计信息
        if '图片修改日期' in merged_df.columns:
            try:
                # 统计有效的修改日期
                valid_dates = merged_df['图片修改日期'].dropna()
                valid_dates = valid_dates[valid_dates != ""]
                
                print(f"\n图片修改日期统计:")
                print(f"  总图片数: {len(merged_df)}")
                print(f"  成功获取修改日期的图片数: {len(valid_dates)}")
                print(f"  失败/缺失的图片数: {len(merged_df) - len(valid_dates)}")
                
                if len(valid_dates) > 0:
                    # 显示最早的5个修改日期
                    print("  最早的5个修改日期:")
                    for date in sorted(valid_dates.unique())[:5]:
                        count = (valid_dates == date).sum()
                        print(f"    {date}: {count}个文件")
                
                # 显示G列的位置
                g_column_index = merged_df.columns.get_loc('图片修改日期')
                print(f"  '图片修改日期'列位于第 {g_column_index + 1} 列（{chr(65 + g_column_index)}列）")
                
            except Exception as e:
                print(f"显示图片修改日期统计信息时出错: {e}")
        
        # 显示源文件信息
        if 'source_file' in merged_df.columns:
            file_counts = merged_df['source_file'].value_counts()
            print("\n各源文件贡献的行数:")
            for file, count in file_counts.items():
                print(f"  {file}: {count} 行")
                
    except Exception as e:
        print(f"处理数据时出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("开始合并最新的CSV文件（处理列结构不匹配）...")
    print("=" * 50)
    merge_latest_csv_files()
    print("=" * 50)
    print("处理完成！")

if __name__ == "__main__":
    main()
