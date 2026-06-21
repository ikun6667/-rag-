"""测试分块逻辑"""
from app.rag.data_processor import DataProcessor
import os

dp = DataProcessor()

# 测试所有文件
knowledge_dir = "data/knowledge"
for root, dirs, files in os.walk(knowledge_dir):
    for file in files:
        if file.endswith('.txt'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                chunks = dp.chunk_text(text)
                print(f"{file}: 长度={len(text)}, 分块数={len(chunks)}")

print("\n所有文件处理完成！")
