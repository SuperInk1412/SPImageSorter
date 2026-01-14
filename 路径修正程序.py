#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV图片路径纠正工具
功能：纠正CSV文件中错误的图片路径，自动搜索并替换为正确的绝对路径
"""

import os
import sys
import csv
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
from pathlib import Path, PureWindowsPath
import threading
import queue
import traceback
from typing import List, Tuple, Optional, Dict
import chardet

class CSVPathCorrector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CSV图片路径纠正工具")
        self.root.geometry("900x700")
        
        # 设置程序图标（如果有的话）
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # 变量初始化
        self.csv_file_path = tk.StringVar()
        self.search_folders = []  # 存储要搜索的文件夹路径
        self.output_file_path = tk.StringVar(value="corrected_output.csv")
        self.processing = False
        self.log_queue = queue.Queue()
        
        # 创建UI
        self.setup_ui()
        
        # 启动日志更新线程
        self.start_log_updater()
    
    def setup_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # CSV文件选择部分
        ttk.Label(main_frame, text="CSV文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.csv_file_path, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(main_frame, text="浏览...", command=self.browse_csv).grid(row=0, column=2, padx=(0, 5))
        
        # 搜索文件夹列表
        ttk.Label(main_frame, text="搜索文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # 创建框架用于文件夹列表和按钮
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 文件夹列表框和滚动条
        self.folder_listbox = tk.Listbox(folder_frame, height=6)
        folder_scrollbar = ttk.Scrollbar(folder_frame, orient=tk.VERTICAL, command=self.folder_listbox.yview)
        self.folder_listbox.config(yscrollcommand=folder_scrollbar.set)
        
        self.folder_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        folder_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置文件夹列表框所在框架的网格权重
        folder_frame.columnconfigure(0, weight=1)
        folder_frame.rowconfigure(0, weight=1)
        
        # 文件夹操作按钮框架
        folder_btn_frame = ttk.Frame(main_frame)
        folder_btn_frame.grid(row=1, column=3, sticky=tk.N, padx=(5, 0))
        
        ttk.Button(folder_btn_frame, text="添加文件夹", command=self.add_search_folder).grid(row=0, column=0, pady=2, sticky=tk.W)
        ttk.Button(folder_btn_frame, text="移除选中", command=self.remove_selected_folder).grid(row=1, column=0, pady=2, sticky=tk.W)
        ttk.Button(folder_btn_frame, text="清空列表", command=self.clear_folders).grid(row=2, column=0, pady=2, sticky=tk.W)
        
        # 输出文件设置
        ttk.Label(main_frame, text="输出文件:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_file_path, width=60).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(main_frame, text="浏览...", command=self.browse_output).grid(row=2, column=2, padx=(0, 5))
        
        # 选项设置
        ttk.Label(main_frame, text="选项:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=3, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.create_missing_only_var = tk.BooleanVar(value=True)
        self.keep_original_order_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="仅处理找不到的图片", 
                        variable=self.create_missing_only_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="保持CSV原始顺序", 
                        variable=self.keep_original_order_var).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=4, pady=20)
        
        self.start_button = ttk.Button(control_frame, text="开始处理", command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(control_frame, text="退出", command=self.root.quit).grid(row=0, column=1, padx=5)
        
        # 日志输出
        ttk.Label(main_frame, text="处理日志:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        # 创建滚动文本区域
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=100, state='disabled')
        self.log_text.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 配置主框架的行列权重
        for i in range(7):
            main_frame.rowconfigure(i, weight=0)
        main_frame.rowconfigure(6, weight=1)
        
        for i in range(4):
            main_frame.columnconfigure(i, weight=0)
        main_frame.columnconfigure(1, weight=1)
    
    def browse_csv(self):
        """浏览选择CSV文件"""
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.csv_file_path.set(file_path)
            # 自动生成输出文件名
            csv_path = Path(file_path)
            output_name = csv_path.stem + "_corrected" + csv_path.suffix
            self.output_file_path.set(str(csv_path.parent / output_name))
    
    def add_search_folder(self):
        """添加搜索文件夹"""
        folder_path = filedialog.askdirectory(title="选择搜索文件夹")
        if folder_path:
            folder_path = self.normalize_path(folder_path)
            if folder_path not in self.search_folders:
                self.search_folders.append(folder_path)
                self.update_folder_listbox()
    
    def remove_selected_folder(self):
        """移除选中的文件夹"""
        selection = self.folder_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.search_folders):
                del self.search_folders[index]
                self.update_folder_listbox()
    
    def clear_folders(self):
        """清空文件夹列表"""
        self.search_folders = []
        self.update_folder_listbox()
    
    def update_folder_listbox(self):
        """更新文件夹列表框"""
        self.folder_listbox.delete(0, tk.END)
        for folder in self.search_folders:
            self.folder_listbox.insert(tk.END, folder)
    
    def browse_output(self):
        """浏览选择输出文件"""
        file_path = filedialog.asksaveasfilename(
            title="选择输出文件",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.output_file_path.set(file_path)
    
    def normalize_path(self, path_str: str) -> str:
        """规范化路径，将反斜杠转换为正斜杠，并确保是绝对路径"""
        # 先使用pathlib处理路径
        path = Path(path_str)
        
        # 如果是相对路径，转换为绝对路径
        if not path.is_absolute():
            # 相对于程序所在目录
            program_dir = Path(sys.argv[0]).parent
            path = (program_dir / path).resolve()
        
        # 返回统一格式的路径字符串（使用正斜杠）
        return str(path).replace('\\', '/')
    
    def detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            
            # 检查是否有BOM
            if raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            elif raw_data.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            elif raw_data.startswith(b'\xfe\xff'):
                return 'utf-16-be'
            
            return encoding or 'utf-8'
    
    def read_csv(self, file_path: str) -> Tuple[List[List[str]], str]:
        """读取CSV文件"""
        encoding = self.detect_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            # 使用csv.reader读取
            reader = csv.reader(f)
            rows = [row for row in reader]
        
        return rows, encoding
    
    def write_csv(self, file_path: str, rows: List[List[str]], encoding: str = 'utf-8-sig'):
        """写入CSV文件"""
        with open(file_path, 'w', encoding=encoding, newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    def find_image_files(self, filename: str, search_folders: List[str]) -> List[str]:
        """在指定文件夹中查找图片文件"""
        found_files = []
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        
        for folder in search_folders:
            folder_path = Path(folder)
            if not folder_path.exists():
                continue
            
            # 先尝试精确匹配
            for ext in extensions:
                # 检查原文件名是否已有扩展名
                if Path(filename).suffix:
                    # 原文件名已有扩展名
                    target_path = folder_path / filename
                    if target_path.exists() and target_path.is_file():
                        found_files.append(str(target_path))
                else:
                    # 原文件名无扩展名，尝试各种扩展名
                    target_path = folder_path / (filename + ext)
                    if target_path.exists() and target_path.is_file():
                        found_files.append(str(target_path))
                    
                    # 也尝试大小写变化
                    target_path = folder_path / (filename + ext.upper())
                    if target_path.exists() and target_path.is_file():
                        found_files.append(str(target_path))
            
            # 如果还没有找到，尝试不区分大小写的搜索
            if not found_files:
                try:
                    for file_path in folder_path.rglob('*'):
                        if file_path.is_file():
                            if file_path.name.lower() == filename.lower():
                                found_files.append(str(file_path))
                            elif file_path.stem.lower() == Path(filename).stem.lower():
                                found_files.append(str(file_path))
                except (PermissionError, OSError) as e:
                    self.log_message(f"无法访问文件夹 {folder}: {e}")
        
        # 规范化路径
        found_files = [self.normalize_path(f) for f in found_files]
        return found_files
    
    def process_csv(self):
        """处理CSV文件的主要逻辑"""
        try:
            csv_path_str = self.csv_file_path.get().strip()
            if not csv_path_str:
                self.log_message("错误：请先选择CSV文件")
                return
            
            csv_path = Path(csv_path_str)
            if not csv_path.exists():
                self.log_message(f"错误：CSV文件不存在 - {csv_path}")
                return
            
            output_path_str = self.output_file_path.get().strip()
            if not output_path_str:
                self.log_message("错误：请指定输出文件路径")
                return
            
            output_path = Path(output_path_str)
            
            # 检查搜索文件夹
            if not self.search_folders:
                self.log_message("警告：没有指定搜索文件夹，将只检查现有路径")
            
            # 读取CSV
            self.log_message(f"正在读取CSV文件: {csv_path}")
            rows, encoding = self.read_csv(csv_path_str)
            
            if not rows:
                self.log_message("错误：CSV文件为空或读取失败")
                return
            
            self.log_message(f"CSV编码: {encoding}")
            self.log_message(f"找到 {len(rows)} 行数据")
            
            # 获取程序所在目录作为根目录
            program_dir = Path(sys.argv[0]).parent.resolve()
            
            # 统计信息
            total_rows = len(rows)
            corrected_count = 0
            missing_count = 0
            multiple_found_count = 0
            
            # 处理每一行
            processed_rows = []
            for i, row in enumerate(rows):
                if not row:  # 跳过空行
                    processed_rows.append(row)
                    continue
                
                # 获取第一列的路径
                original_path = row[0].strip() if len(row) > 0 else ""
                
                if not original_path:  # 空路径
                    processed_rows.append(row)
                    self.log_message(f"第 {i+1} 行: 图片路径为空，跳过")
                    continue
                
                # 规范化原始路径
                normalized_original = self.normalize_path(original_path)
                image_path = Path(normalized_original)
                
                # 检查图片是否存在
                if image_path.exists() and image_path.is_file():
                    # 图片存在，使用规范化后的路径
                    new_row = [self.normalize_path(str(image_path))] + row[1:]
                    processed_rows.append(new_row)
                    self.log_message(f"第 {i+1} 行: 图片存在 - {image_path.name}")
                else:
                    # 图片不存在，尝试在搜索文件夹中查找
                    missing_count += 1
                    filename = image_path.name
                    
                    if not filename:
                        self.log_message(f"第 {i+1} 行: 无法提取文件名，保持原样")
                        processed_rows.append(row)
                        continue
                    
                    self.log_message(f"第 {i+1} 行: 图片不存在 - {original_path}")
                    self.log_message(f"  正在搜索文件: {filename}")
                    
                    # 在搜索文件夹中查找
                    found_files = self.find_image_files(filename, self.search_folders)
                    
                    if len(found_files) == 1:
                        # 找到唯一匹配
                        new_path = found_files[0]
                        new_row = [new_path] + row[1:]
                        processed_rows.append(new_row)
                        corrected_count += 1
                        self.log_message(f"  找到文件: {new_path}")
                    elif len(found_files) > 1:
                        # 找到多个匹配
                        multiple_found_count += 1
                        if self.keep_original_order_var.get():
                            # 保持原始顺序，使用第一个找到的
                            new_path = found_files[0]
                            new_row = [new_path] + row[1:]
                            processed_rows.append(new_row)
                            corrected_count += 1
                            self.log_message(f"  找到 {len(found_files)} 个匹配文件，使用第一个: {new_path}")
                            for j, found in enumerate(found_files[1:], 1):
                                self.log_message(f"    备选 {j}: {found}")
                        else:
                            # 创建多行，每个匹配文件一行
                            self.log_message(f"  找到 {len(found_files)} 个匹配文件，创建 {len(found_files)} 行:")
                            for j, found in enumerate(found_files):
                                new_row = [found] + row[1:]
                                processed_rows.append(new_row)
                                self.log_message(f"    行 {j+1}: {found}")
                            corrected_count += len(found_files)
                    else:
                        # 没有找到
                        if self.create_missing_only_var.get():
                            # 只处理找不到的图片，保持原样
                            processed_rows.append(row)
                            self.log_message(f"  未找到文件，保持原路径")
                        else:
                            # 删除这一行
                            self.log_message(f"  未找到文件，删除该行")
            
            # 写入输出文件
            self.log_message(f"\n正在写入输出文件: {output_path}")
            self.write_csv(str(output_path), processed_rows, encoding)
            
            # 显示统计信息
            self.log_message("\n" + "="*50)
            self.log_message("处理完成!")
            self.log_message(f"总行数: {total_rows}")
            self.log_message(f"缺失图片: {missing_count}")
            self.log_message(f"已纠正: {corrected_count}")
            self.log_message(f"多个匹配文件的情况: {multiple_found_count}")
            self.log_message(f"输出文件: {output_path}")
            
            # 显示完成消息
            messagebox.showinfo("处理完成", 
                f"CSV文件处理完成！\n\n"
                f"总行数: {total_rows}\n"
                f"缺失图片: {missing_count}\n"
                f"已纠正: {corrected_count}\n"
                f"多个匹配文件的情况: {multiple_found_count}\n\n"
                f"输出文件: {output_path.name}")
            
        except Exception as e:
            self.log_message(f"\n错误: {str(e)}")
            self.log_message(traceback.format_exc())
            messagebox.showerror("处理错误", f"处理过程中发生错误:\n{str(e)}")
        finally:
            self.processing = False
            self.start_button.config(state=tk.NORMAL)
            self.root.title("CSV图片路径纠正工具")
    
    def start_processing(self):
        """开始处理"""
        if self.processing:
            return
        
        # 验证输入
        if not self.csv_file_path.get().strip():
            messagebox.showerror("错误", "请先选择CSV文件")
            return
        
        # 清除日志
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        # 开始处理
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.root.title("CSV图片路径纠正工具 - 处理中...")
        
        # 在新线程中处理
        thread = threading.Thread(target=self.process_csv, daemon=True)
        thread.start()
    
    def log_message(self, message: str):
        """添加日志消息"""
        self.log_queue.put(message)
    
    def update_log(self):
        """更新日志显示"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')
        except queue.Empty:
            pass
        
        # 继续调度更新
        self.root.after(100, self.update_log)
    
    def start_log_updater(self):
        """启动日志更新器"""
        self.root.after(100, self.update_log)
    
    def run(self):
        """运行程序"""
        self.root.mainloop()

def main():
    """主函数"""
    # 设置DPI感知，改善高DPI显示
    if sys.platform == 'win32':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    # 创建并运行应用
    app = CSVPathCorrector()
    app.run()

if __name__ == "__main__":
    main()
