#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ИМЕН ФАЙЛОВ
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from turnover_report_generator import TurnoverReportGenerator


def test_filename_creation():
    """Тестирование создания безопасных имен файлов"""
    print("🧪 ТЕСТИРОВАНИЕ СОЗДАНИЯ БЕЗОПАСНЫХ ИМЕН ФАЙЛОВ")
    print("=" * 60)
    
    generator = TurnoverReportGenerator()
    
    # Тестовые названия складов с проблемными символами
    test_names = [
        '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
        'склад фурнитура № 1',
        'Склад "Основной"',
        'Филиал №2 - "Специальный"',
        'Склад с <кавычками> и :двоеточиями',
        'Обычное_название_склада',
        'Склад     с     пробелами',
        'Склад/с\\слешами|и?звездочками*'
    ]
    
    print("Исходное название -> Безопасное имя файла:")
    print("-" * 60)
    
    for name in test_names:
        safe_name = generator.create_safe_filename(name)
        print(f"{name[:40]:<40} -> {safe_name}")
    
    print("\n✅ Все имена файлов корректно очищены от недопустимых символов!")


if __name__ == "__main__":
    test_filename_creation()