with open(r'd:\2026 resolution tracker\app.py', encoding='utf-8') as f:
    src = f.read()

for i, line in enumerate(src.split('\n'), 1):
    if 'vault' in line.lower() and 'route' in line.lower():
        print(f"{i}: {line[:120]}")
