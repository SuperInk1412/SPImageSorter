import os
import glob
import shutil
import pathlib

def get_latest_txt_by_mtime(folder_path):
    """
    获取文件夹内最新的txt文件（按修改时间排序）
    """
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"在文件夹 {folder_path} 中未找到任何txt文件")
    
    # 按修改时间排序，最新的在前
    txt_files.sort(key=os.path.getmtime, reverse=True)
    return txt_files[0]  # 返回最新的文件

def extract_file_path_from_txt(txt_file):
    """
    从txt文件中提取文件路径
    规则：找到以"Tags of "开头的最后一行
    """
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 逆序遍历，找到第一个包含"Tags of "的行
    for line in reversed(lines):
        if line.startswith("Tags of "):
            # 提取文件路径部分（去掉"Tags of "和可能的尾随空格/冒号）
            file_path = line[len("Tags of "):].strip()
            # 清理可能的额外字符
            if file_path.endswith(':'):
                file_path = file_path[:-1].strip()
            return file_path
    
    raise ValueError(f"在文件 {txt_file} 中未找到以'Tags of '开头的行")

def move_file_to_target(source_file_path, script_dir):
    """
    将源文件移动到目标目录
    """
    # 目标目录：py所在目录\未处理\无法分类
    target_dir = os.path.join(script_dir, "未处理", "无法分类")
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 检查源文件是否存在
    if not os.path.exists(source_file_path):
        raise FileNotFoundError(f"源文件不存在: {source_file_path}")
    
    # 获取文件名
    file_name = os.path.basename(source_file_path)
    
    # 目标路径
    target_path = os.path.join(target_dir, file_name)
    
    # 移动文件（如果目标文件已存在，添加数字后缀）
    counter = 1
    name_part, ext_part = os.path.splitext(file_name)
    while os.path.exists(target_path):
        target_path = os.path.join(target_dir, f"{name_part}_{counter}{ext_part}")
        counter += 1
    
    shutil.move(source_file_path, target_path)
    print(f"文件已移动: {source_file_path} -> {target_path}")
    return target_path

def main():
    """
    主函数
    """
    try:
        # 1. 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"脚本所在目录: {script_dir}")
        
        # 2. 构建Exported_Labels文件夹路径
        labels_folder = os.path.join(script_dir, "Exported_Labels")
        print(f"标签文件夹路径: {labels_folder}")
        
        # 3. 获取最新的txt文件
        latest_txt = get_latest_txt_by_mtime(labels_folder)
        print(f"找到最新的txt文件: {latest_txt}")
        
        # 4. 从txt文件中提取文件路径
        source_file_path = extract_file_path_from_txt(latest_txt)
        print(f"从txt中提取的文件路径: {source_file_path}")
        
        # 5. 验证提取的路径是否有效
        if not os.path.isabs(source_file_path):
            print("警告：提取的路径不是绝对路径，尝试在脚本目录下查找...")
            # 尝试在脚本目录下查找相对路径
            possible_path = os.path.join(script_dir, source_file_path)
            if os.path.exists(possible_path):
                source_file_path = possible_path
            else:
                raise FileNotFoundError(f"无法解析文件路径: {source_file_path}")
        
        # 6. 移动文件
        target_path = move_file_to_target(source_file_path, script_dir)
        
        print("操作完成！")
        return True
        
    except FileNotFoundError as e:
        print(f"错误：{e}")
        return False
    except ValueError as e:
        print(f"错误：{e}")
        return False
    except Exception as e:
        print(f"意外错误：{e}")
        return False

if __name__ == "__main__":
    # 运行程序
    success = main()
    if not success:
        print("程序执行失败")
