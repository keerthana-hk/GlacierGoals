import os
from jinja2 import Environment, FileSystemLoader

try:
    template_dir = r'd:\2026 resolution tracker\templates'
    env = Environment(loader=FileSystemLoader(template_dir))
    env.get_template('base.html')
    print("base.html is valid Jinja")
except Exception as e:
    import traceback
    print(f"Jinja Error: {e}")
    traceback.print_exc()
