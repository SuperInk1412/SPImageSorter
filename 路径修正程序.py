#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV图片路径纠正工具 - 高性能版
优化点：
1. 使用文件系统索引加速搜索
2. 改进多线程任务分配
3. 优化缓存机制
4. 使用更高效的文件名匹配算法
5. 添加性能监控
"""

import os
import sys
import csv
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
from pathlib import Path
import threading
import queue
import traceback
from typing import List, Tuple, Dict, Set
import chardet
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import fnmatch
from collections import defaultdict

class CSVPathCorrector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CSV图片路径纠正工具 - 高性能版")
        self.root.geometry("900x700")
        
        # 变量初始化
        self.csv_file_path = tk.StringVar()
        self.search_folders = []
        self.output_file_path = tk.StringVar(value="corrected_output.csv")
        self.processing = False
        self.log_queue = queue.Queue()
        self.file_index = defaultdict(set)  # 文件名小写 -> 完整路径集合
        self.folder_cache = set()  # 已索引的文件夹
        self.stop_event = threading.Event()
        self.performance_stats = {
            'total_files': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'search_time': 0.0
        }
        
        # 创建UI
        self.setup_ui()
        
        # 启动日志更新线程
        self.start_log_updater()
    
    def setup_ui(self):
        """创建用户界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # CSV文件选择部分
        ttk.Label(main_frame, text="CSV文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.csv_file_path, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(main_frame, text="浏览...", command=self.browse_csv).grid(row=0, column=2, padx=(0, 5))
        
        # 搜索文件夹列表
        ttk.Label(main_frame, text="搜索文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.folder_listbox = tk.Listbox(folder_frame, height=6)
        folder_scrollbar = ttk.Scrollbar(folder_frame, orient=tk.VERTICAL, command=self.folder_listbox.yview)
        self.folder_listbox.config(yscrollcommand=folder_scrollbar.set)
        
        self.folder_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        folder_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        folder_frame.columnconfigure(0, weight=1)
        folder_frame.rowconfigure(0, weight=1)
        
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
        self.use_multithreading_var = tk.BooleanVar(value=True)
        self.use_file_cache_var = tk.BooleanVar(value=True)
        self.use_fast_search_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="仅处理找不到的图片", 
                        variable=self.create_missing_only_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="保持CSV原始顺序", 
                        variable=self.keep_original_order_var).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Checkbutton(options_frame, text="启用多线程搜索", 
                        variable=self.use_multithreading_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="启用文件缓存", 
                        variable=self.use_file_cache_var).grid(row=1, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Checkbutton(options_frame, text="启用快速搜索", 
                        variable=self.use_fast_search_var).grid(row=2, column=0, sticky=tk.W)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=5, column=0, columnspan=4, pady=20)
        
        self.start_button = ttk.Button(control_frame, text="开始处理", command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(control_frame, text="停止", command=self.stop_processing).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="退出", command=self.root.quit).grid(row=0, column=2, padx=5)
        
        # 日志输出
        ttk.Label(main_frame, text="处理日志:").grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=100, state='disabled')
        self.log_text.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 配置主框架的行列权重
        for i in range(8):
            main_frame.rowconfigure(i, weight=0)
        main_frame.rowconfigure(7, weight=1)
        
        for i in range(4):
            main_frame.columnconfigure(i, weight=0)
        main_frame.columnconfigure(1, weight=1)
    
    def browse_csv(self):
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.csv_file_path.set(file_path)
            csv_path = Path(file_path)
            output_name = csv_path.stem + "_corrected" + csv_path.suffix
            self.output_file_path.set(str(csv_path.parent / output_name))
    
    def add_search_folder(self):
        folder_path = filedialog.askdirectory(title="选择搜索文件夹")
        if folder_path:
            folder_path = self.normalize_path(folder_path)
            if folder_path not in self.search_folders:
                self.search_folders.append(folder_path)
                self.update_folder_listbox()
    
    def remove_selected_folder(self):
        selection = self.folder_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.search_folders):
                del self.search_folders[index]
                self.update_folder_listbox()
    
    def clear_folders(self):
        self.search_folders = []
        self.update_folder_listbox()
    
    def update_folder_listbox(self):
        self.folder_listbox.delete(0, tk.END)
        for folder in self.search_folders:
            self.folder_listbox.insert(tk.END, folder)
    
    def browse_output(self):
        file_path = filedialog.asksaveasfilename(
            title="选择输出文件",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.output_file_path.set(file_path)
    
    def normalize_path(self, path_str: str) -> str:
        path = Path(path_str)
        if not path.is_absolute():
            program_dir = Path(sys.argv[0]).parent
            path = (program_dir / path).resolve()
        return str(path).replace('\\', '/')
    
    def detect_encoding(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            
            if raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            elif raw_data.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            elif raw_data.startswith(b'\xfe\xff'):
                return 'utf-16-be'
            
            return encoding or 'utf-8'
    
    def read_csv(self, file_path: str) -> Tuple[List[List[str]], str]:
        encoding = self.detect_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
        
        return rows, encoding
    
    def write_csv(self, file_path: str, rows: List[List[str]], encoding: str = 'utf-8-sig'):
        with open(file_path, 'w', encoding=encoding, newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    def build_file_index(self, folder_path: str) -> bool:
        """构建文件索引，返回是否成功"""
        if folder_path in self.folder_cache:
            return True
            
        folder = Path(folder_path)
        if not folder.exists():
            return False
        
        try:
            start_time = time.time()
            file_count = 0
            
            for root, _, files in os.walk(folder_path):
                if self.stop_event.is_set():
                    return False
                
                for file in files:
                    file_lower = file.lower()
                    full_path = os.path.join(root, file)
                    self.file_index[file_lower].add(full_path)
                    file_count += 1
            
            self.folder_cache.add(folder_path)
            self.performance_stats['total_files'] += file_count
            elapsed = time.time() - start_time
            self.log_message(f"已索引文件夹 {folder_path} (共 {file_count} 个文件, 耗时 {elapsed:.2f}秒)")
            return True
        except (PermissionError, OSError) as e:
            self.log_message(f"无法索引文件夹 {folder_path}: {e}")
            return False
    
    def fast_search_files(self, filename: str) -> List[str]:
        """使用文件索引快速搜索文件"""
        start_time = time.time()
        filename_lower = filename.lower()
        filename_stem = Path(filename).stem.lower()
        found_files = set()
        
        # 精确匹配
        if filename_lower in self.file_index:
            found_files.update(self.file_index[filename_lower])
        
        # 如果没有扩展名，尝试常见图片扩展名
        if not Path(filename).suffix:
            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
                test_name = filename + ext
                test_name_lower = test_name.lower()
                if test_name_lower in self.file_index:
                    found_files.update(self.file_index[test_name_lower])
        
        # 尝试匹配文件名主干
        for indexed_file in self.file_index:
            if Path(indexed_file).stem.lower() == filename_stem:
                found_files.update(self.file_index[indexed_file])
        
        # 转换为规范化路径列表
        result = [self.normalize_path(f) for f in found_files]
        
        elapsed = time.time() - start_time
        self.performance_stats['search_time'] += elapsed
        return result
    
    def find_image_files(self, filename: str) -> List[str]:
        """查找图片文件，根据设置选择搜索方式"""
        if self.use_fast_search_var.get() and self.use_file_cache_var.get():
            return self.fast_search_files(filename)
        
        # 传统搜索方式（不使用索引）
        filename_lower = filename.lower()
        filename_stem = Path(filename).stem.lower()
        found_files = set()
        
        def search_in_folder(folder: str):
            try:
                for root, _, files in os.walk(folder):
                    if self.stop_event.is_set():
                        return
                    
                    for file in files:
                        file_lower = file.lower()
                        
                        # 精确匹配
                        if file_lower == filename_lower:
                            found_files.add(os.path.join(root, file))
                            continue
                        
                        # 如果没有扩展名，尝试常见图片扩展名
                        if not Path(filename).suffix:
                            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
                                if file_lower == (filename + ext).lower():
                                    found_files.add(os.path.join(root, file))
                                    break
                        
                        # 尝试匹配文件名主干
                        if Path(file).stem.lower() == filename_stem:
                            found_files.add(os.path.join(root, file))
            except (PermissionError, OSError) as e:
                self.log_message(f"搜索文件夹 {folder} 时出错: {e}")
        
        if self.use_multithreading_var.get():
            with ThreadPoolExecutor(max_workers=min(8, len(self.search_folders))) as executor:
                futures = {executor.submit(search_in_folder, folder): folder for folder in self.search_folders}
                
                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        break
        else:
            for folder in self.search_folders:
                if self.stop_event.is_set():
                    break
                search_in_folder(folder)
        
        return [self.normalize_path(f) for f in found_files]
    
    def process_csv(self):
        try:
            self.stop_event.clear()
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
            
            # 构建文件索引
            if self.use_file_cache_var.get() and self.use_fast_search_var.get():
                self.log_message("正在构建文件索引...")
                start_index_time = time.time()
                
                if self.use_multithreading_var.get():
                    with ThreadPoolExecutor(max_workers=min(8, len(self.search_folders))) as executor:
                        futures = {executor.submit(self.build_file_index, folder): folder for folder in self.search_folders}
                        
                        for future in as_completed(futures):
                            if self.stop_event.is_set():
                                break
                else:
                    for folder in self.search_folders:
                        if self.stop_event.is_set():
                            break
                        self.build_file_index(folder)
                
                elapsed = time.time() - start_index_time
                self.log_message(f"文件索引构建完成，耗时 {elapsed:.2f}秒")
                self.log_message(f"已索引 {self.performance_stats['total_files']} 个文件")
            
            # 处理每一行
            processed_rows = []
            total_rows = len(rows)
            corrected_count = 0
            missing_count = 0
            multiple_found_count = 0
            
            start_time = time.time()
            last_update_time = start_time
            
            for i, row in enumerate(rows):
                if self.stop_event.is_set():
                    self.log_message("处理已中止")
                    break
                
                # 更新进度
                current_time = time.time()
                if current_time - last_update_time > 0.5:
                    progress = (i + 1) / total_rows * 100
                    self.progress_var.set(progress)
                    self.root.update_idletasks()
                    last_update_time = current_time
                
                if not row:
                    processed_rows.append(row)
                    continue
                
                original_path = row[0].strip() if len(row) > 0 else ""
                
                if not original_path:
                    processed_rows.append(row)
                    continue
                
                normalized_original = self.normalize_path(original_path)
                image_path = Path(normalized_original)
                
                if image_path.exists() and image_path.is_file():
                    new_row = [self.normalize_path(str(image_path))] + row[1:]
                    processed_rows.append(new_row)
                else:
                    missing_count += 1
                    filename = image_path.name
                    
                    if not filename:
                        processed_rows.append(row)
                        continue
                    
                    found_files = self.find_image_files(filename)
                    
                    if len(found_files) == 1:
                        new_path = found_files[0]
                        new_row = [new_path] + row[1:]
                        processed_rows.append(new_row)
                        corrected_count += 1
                    elif len(found_files) > 1:
                        multiple_found_count += 1
                        if self.keep_original_order_var.get():
                            new_path = found_files[0]
                            new_row = [new_path] + row[1:]
                            processed_rows.append(new_row)
                            corrected_count += 1
                        else:
                            for found in found_files:
                                new_row = [found] + row[1:]
                                processed_rows.append(new_row)
                            corrected_count += len(found_files)
                    else:
                        if self.create_missing_only_var.get():
                            processed_rows.append(row)
            
            self.progress_var.set(100)
            
            if not self.stop_event.is_set():
                self.log_message(f"\n正在写入输出文件: {output_path}")
                self.write_csv(str(output_path), processed_rows, encoding)
                
                elapsed_time = time.time() - start_time
                self.log_message("\n" + "="*50)
                self.log_message("处理完成!")
                self.log_message(f"总行数: {total_rows}")
                self.log_message(f"缺失图片: {missing_count}")
                self.log_message(f"已纠正: {corrected_count}")
                self.log_message(f"多个匹配文件的情况: {multiple_found_count}")
                self.log_message(f"总耗时: {elapsed_time:.2f}秒")
                
                if self.use_fast_search_var.get():
                    avg_search_time = (self.performance_stats['search_time'] / max(1, missing_count)) * 1000
                    self.log_message(f"平均搜索时间: {avg_search_time:.2f}毫秒/文件")
                
                messagebox.showinfo("处理完成", 
                    f"CSV文件处理完成！\n\n"
                    f"总行数: {total_rows}\n"
                    f"缺失图片: {missing_count}\n"
                    f"已纠正: {corrected_count}\n"
                    f"多个匹配文件的情况: {multiple_found_count}\n"
                    f"总耗时: {elapsed_time:.2f}秒\n\n"
                    f"输出文件: {output_path.name}")
            
        except Exception as e:
            self.log_message(f"\n错误: {str(e)}")
            self.log_message(traceback.format_exc())
            messagebox.showerror("处理错误", f"处理过程中发生错误:\n{str(e)}")
        finally:
            self.processing = False
            self.start_button.config(state=tk.NORMAL)
            self.root.title("CSV图片路径纠正工具 - 高性能版")
            self.file_index.clear()
            self.folder_cache.clear()
            self.performance_stats = {
                'total_files': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'search_time': 0.0
            }
    
    def start_processing(self):
        if self.processing:
            return
        
        if not self.csv_file_path.get().strip():
            messagebox.showerror("错误", "请先选择CSV文件")
            return
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        self.file_index.clear()
        self.folder_cache.clear()
        self.performance_stats = {
            'total_files': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'search_time': 0.0
        }
        self.progress_var.set(0)
        
        self.processing = True
        self.stop_event.clear()
        self.start_button.config(state=tk.DISABLED)
        self.root.title("CSV图片路径纠正工具 - 处理中...")
        
        thread = threading.Thread(target=self.process_csv, daemon=True)
        thread.start()
    
    def stop_processing(self):
        if self.processing:
            self.stop_event.set()
            self.log_message("\n正在停止处理...")
    
    def log_message(self, message: str):
        self.log_queue.put(message)
    
    def update_log(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')
        except queue.Empty:
            pass
        
        self.root.after(100, self.update_log)
    
    def start_log_updater(self):
        self.root.after(100, self.update_log)
    
    def run(self):
        self.root.mainloop()

def main():
    if sys.platform == 'win32':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    app = CSVPathCorrector()
    app.run()

if __name__ == "__main__":
    main()
