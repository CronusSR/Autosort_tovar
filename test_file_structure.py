#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование структуры файла продаж для проверки маппинга
"""

import sys
import os

def test_file_structure():
    """Тестируем обработчик на реальном файле"""
    filename = "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx"
    
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден!")
        return
    
    try:
        # Пытаемся использовать наш обработчик
        from single_file_ads_processor import SingleFileADSProcessor
        
        processor = SingleFileADSProcessor()
        
        # Имитируем загрузку файла
        with open(filename, 'rb') as f:
            file_content = f.read()
        
        # Создаем объект-заглушку для uploaded_file
        class MockUploadedFile:
            def __init__(self, content):
                self.content = content
            
            def read(self):
                return self.content
        
        mock_file = MockUploadedFile(file_content)
        
        # Тестируем обработку
        print("🔍 Тестируем обработку файла...")
        results = processor.process_single_file(mock_file)
        
        if results['success']:
            print(f"✅ Файл успешно обработан!")
            print(f"📊 Найдено филиалов: {results['total_branches']}")
            print(f"📦 Всего товаров: {results['total_items']}")
            
            print("\n📋 Детали по филиалам:")
            for branch_name, branch_data in results['branches_data'].items():
                print(f"  • {branch_data['branch_name']}")
                print(f"    Системное имя: {branch_name}")
                print(f"    Товаров: {branch_data['total_items']}")
        else:
            print("❌ Ошибки при обработке:")
            for error in results['errors']:
                print(f"  • {error}")
                
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Попробуем прочитать файл напрямую...")
        
        # Альтернативный способ без pandas
        try:
            import openpyxl
            
            wb = openpyxl.load_workbook(filename)
            ws = wb.active
            
            # Читаем первую строку (заголовки)
            headers = []
            for cell in ws[1]:
                if cell.value:
                    headers.append(str(cell.value))
            
            print(f"\n📋 Найденные колонки ({len(headers)}):")
            for i, header in enumerate(headers):
                print(f"{i+1:2d}. {header}")
                
            # Тестируем маппинг
            from single_file_ads_processor import SingleFileADSProcessor
            processor = SingleFileADSProcessor()
            branch_columns = processor.identify_branch_columns(headers)
            
            print(f"\n🎯 Определенные филиалы ({len(branch_columns)}):")
            for column, system_name in branch_columns.items():
                print(f"  • {system_name}: {column}")
                
        except Exception as e2:
            print(f"❌ Ошибка чтения файла: {e2}")
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")

if __name__ == "__main__":
    test_file_structure()