import subprocess
try:
    res = subprocess.check_output(['git', 'diff', 'templates/base.html'], text=True)
    print(res)
except Exception as e:
    print(e)
