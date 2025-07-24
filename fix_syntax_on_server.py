#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ НА СЕРВЕРЕ
Запустить этот скрипт на сервере для исправления синтаксической ошибки
"""

import os
import re

def fix_syntax_error():
    """Исправляет синтаксическую ошибку в webhook_persistent_app.py"""
    
    file_path = "/opt/inventory_system/webhook_persistent_app.py"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден")
        return False
    
    print("🔧 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ")
    print("=" * 50)
    
    # Читаем файл
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем синтаксическую ошибку - убираем лишний else
    old_pattern = """                else:
                    st.write("- Нет данных для отображения")
    
            else:
                st.error("Нет данных для построения графика динамики")"""

    new_pattern = """                else:
                    st.write("- Нет данных для отображения")
            else:
                st.error("Нет данных для построения графика динамики")"""
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ Исправлена структура блока условий")
    else:
        print("⚠️ Паттерн не найден, попробуем другой способ...")
        
        # Альтернативное исправление - ищем проблемную строку
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Ищем проблемную последовательность
            if "st.write(\"- Нет данных для отображения\")" in line:
                fixed_lines.append(line)
                i += 1
                
                # Проверяем следующие строки
                if i < len(lines) and lines[i].strip() == "":
                    # Пропускаем пустую строку
                    i += 1
                
                if i < len(lines) and "else:" in lines[i] and "st.error" in lines[i+1]:
                    # Убираем отступ у else
                    else_line = lines[i].replace("            else:", "        else:")
                    fixed_lines.append(else_line)
                    i += 1
                    
                    # Добавляем следующую строку
                    if i < len(lines):
                        fixed_lines.append(lines[i])
                        i += 1
                else:
                    # Обычное продолжение
                    if i < len(lines):
                        fixed_lines.append(lines[i])
                        i += 1
            else:
                fixed_lines.append(line)
                i += 1
        
        content = '\n'.join(fixed_lines)
        print("✅ Исправлена структура построчно")
    
    # Сохраняем исправленный файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Файл сохранен с исправлениями")
    
    # Проверяем синтаксис
    try:
        compile(content, file_path, 'exec')
        print("✅ Синтаксис корректный")
        return True
    except SyntaxError as e:
        print(f"❌ Все еще есть синтаксическая ошибка: {e}")
        print(f"   Строка {e.lineno}: {e.text}")
        return False

def restart_service():
    """Перезапускает сервис"""
    print("\n🔄 ПЕРЕЗАПУСК СЕРВИСА")
    print("=" * 30)
    
    import subprocess
    
    try:
        # Останавливаем сервис
        subprocess.run(['systemctl', 'stop', 'webhook-analytics'], check=True)
        print("🛑 Сервис остановлен")
        
        # Запускаем сервис
        subprocess.run(['systemctl', 'start', 'webhook-analytics'], check=True)
        print("🔄 Сервис запущен")
        
        # Проверяем статус
        result = subprocess.run(['systemctl', 'is-active', 'webhook-analytics'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip() == 'active':
            print("✅ Сервис работает корректно")
            return True
        else:
            print("❌ Проблемы с сервисом")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка управления сервисом: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ")
    print("=" * 60)
    print("Этот скрипт исправляет синтаксическую ошибку в webhook_persistent_app.py")
    print("")
    
    # Исправляем синтаксис
    if fix_syntax_error():
        print("\n🎉 СИНТАКСИЧЕСКАЯ ОШИБКА ИСПРАВЛЕНА!")
        
        # Перезапускаем сервис
        if restart_service():
            print("\n✅ ВСЕ ГОТОВО!")
            print("🌐 Система доступна: http://217.114.1.117:8502")
            print("\n📊 ИСПРАВЛЕНИЯ:")
            print("   ✅ Убрана лишняя конструкция else")
            print("   ✅ Исправлена структура условных блоков")
            print("   ✅ Динамика продаж должна отображаться корректно")
        else:
            print("\n⚠️ Синтаксис исправлен, но есть проблемы с сервисом")
            print("Проверьте статус: systemctl status webhook-analytics")
    else:
        print("\n❌ НЕ УДАЛОСЬ ИСПРАВИТЬ СИНТАКСИЧЕСКУЮ ОШИБКУ")
        print("Обратитесь за помощью к разработчику")

if __name__ == '__main__':
    main()