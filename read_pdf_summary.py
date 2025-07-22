#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Чтение PDF файла саммари альтернативными методами
"""

import os

def extract_text_from_pdf_simple():
    """Попытка извлечь текст из PDF используя системные утилиты"""
    pdf_file = "самммари.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"Файл {pdf_file} не найден!")
        return
    
    # Пытаемся использовать pdftotext
    print("Пытаемся использовать pdftotext...")
    os.system(f"pdftotext '{pdf_file}' summary_text.txt")
    
    if os.path.exists("summary_text.txt"):
        print("\n=== Содержимое PDF (через pdftotext) ===\n")
        with open("summary_text.txt", "r", encoding="utf-8") as f:
            content = f.read()
            print(content)
            
            # Сохраняем в удобном формате
            with open("summary_content.txt", "w", encoding="utf-8") as out:
                out.write(content)
            
            print("\n✓ Содержимое сохранено в summary_content.txt")
    else:
        print("pdftotext не доступен или не смог прочитать файл")
        
        # Пробуем strings как последний вариант
        print("\nПытаемся извлечь текст через strings...")
        os.system(f"strings '{pdf_file}' > pdf_strings.txt")
        
        if os.path.exists("pdf_strings.txt"):
            print("✓ Строки извлечены в pdf_strings.txt")
            # Показываем первые строки
            os.system("head -50 pdf_strings.txt")

if __name__ == "__main__":
    extract_text_from_pdf_simple()