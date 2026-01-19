# SPImageSorter - 动漫图片分类处理浏览工具

## 项目简介
SPImageSorter 是一个基于 DeepDanbooru 的动漫图片分类处理浏览工具，旨在帮助用户高效管理和检索动漫风格图片。

## 环境准备

### 系统要求
- 操作系统：Windows

### 安装步骤
1. **安装运行依赖**
   - 执行"运行依赖"文件夹中的可执行文件（.exe、.msi）
   - 安装过程中请勾选"添加至PATH"选项

2. **配置命令行环境**
   - 打开命令提示符（cmd）
   - 逐行粘贴以下命令：

pip install tensorflow==2.15.0

pip install tensorflow-io==0.31.0

pip install deepdanbooru

pip install pandas

pip install chardet

3. **等待安装完成**
   - 环境安装预计需要10分钟左右
   - 请耐心等待直至完成

## 使用指南

### 图片分类与检索
1. 将待分类图片放入项目根目录下的 `Images_To_Sort` 文件夹
2. 运行根目录中的 `一键刷新.bat` 脚本
   - 过程中请根据提示按 Enter 键继续
3. 打开 `图片标签数据可视化工具.html`
4. 在可视化工具中导入最新生成的CSV文件
   - 文件位置：`Csv_All` 文件夹内
   - *注意：导入的是CSV文件，不是Csv_All.py*

### 标签翻译功能
- 如需将标签转换为中文，请在可视化工具中导入根目录下的 `中英对照.csv` 文件

### 添加新图片
1. 将新增图片直接放入 `Images_To_Sort` 文件夹
2. 重新运行 `一键刷新.bat`
3. 在可视化工具中导入新生成的CSV文件即可更新数据

### 路径更改功能
如需更改已筛选文件的路径：
1. 在 `Sorted_Images` 文件夹内，将图片剪贴到新路径下
2. 运行 `路径修正程序.py`
3. 添加最新的CSV文件，并指定新路径的文件夹
4. 执行搜索，系统将自动在 `csv_all` 文件夹内生成修正路径后的图片标签数据集

## 注意事项
- **路径规范**：项目根目录的完整路径请勿包含中文字符，否则可能导致图片无法识别
- **项目信息**：
  - 作者：SuperInk
  - 部分代码由AI生成，部分资源基于GitHub开源项目deepdanbooru

## 相关链接
- DeepDanbooru 项目地址：https://github.com/KichangKim/DeepDanbooru
- SuperInk 的 GitHub 主页：https://github.com/SuperInk1412
