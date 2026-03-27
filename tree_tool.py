from pathlib import Path

def display_tree(directory, indent=""):
    path = Path(directory)
    # 遍历当前目录下的所有文件和文件夹
    for item in sorted(path.iterdir()):
        # 跳过隐藏文件和常见的缓存目录
        if item.name.startswith('.') or item.name == "__pycache__":
            continue
            
        print(f"{indent}├── {item.name}")
        
        if item.is_dir():
            display_tree(item, indent + "│   ")

# 使用当前目录
if __name__ == "__main__":
    display_tree('.')