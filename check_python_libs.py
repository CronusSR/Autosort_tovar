import sys
import subprocess

print("Python версия:", sys.version)
print("\nПроверка доступных библиотек:")

libs_to_check = ['pandas', 'openpyxl', 'xlrd', 'csv', 'json', 'sqlite3']

for lib in libs_to_check:
    try:
        __import__(lib)
        print(f"✓ {lib} - установлена")
    except ImportError:
        print(f"✗ {lib} - не установлена")

print("\nПопытка установить pandas...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"], check=True)
    print("Установка завершена!")
except Exception as e:
    print(f"Ошибка установки: {e}")