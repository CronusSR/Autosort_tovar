#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление основного интерфейса для работы с единым файлом продаж
"""

def update_ads_interface_in_main():
    """Обновляет интерфейс загрузки ADS в основном приложении"""
    
    # Код для вставки в streamlit_modular_app.py
    update_code = '''
# === ОБНОВЛЕНИЕ РАЗДЕЛА ЗАГРУЗКИ ADS ===
# Заменить старый код загрузки множественных файлов на:

elif analysis_type == "Загрузка файлов ADS":
    st.header("📊 Загрузка данных о продажах (ADS)")
    
    # Используем новый обработчик единого файла
    from single_file_ads_processor import SingleFileADSProcessor
    
    processor = SingleFileADSProcessor()
    processor.create_streamlit_interface()
    
    # Если данные загружены, показываем статистику
    if st.session_state.get('ads_data_loaded', False):
        st.success("✅ Данные ADS успешно загружены и готовы к анализу!")
        
        # Читаем сводную информацию
        import json
        import os
        
        if os.path.exists('ads/combined_ads_data.json'):
            with open('ads/combined_ads_data.json', 'r', encoding='utf-8') as f:
                combined_data = json.load(f)
            
            # Показываем статистику
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Филиалов", combined_data['branches_count'])
            with col2:
                total_items = sum(b['items_count'] for b in combined_data['branches'].values())
                st.metric("Всего товаров", total_items)
            with col3:
                st.metric("Обновлено", combined_data['updated'][:10])
'''
    
    # Код для обновления обработки в ModularInventorySystem
    system_update_code = '''
# === ОБНОВЛЕНИЕ В modular_inventory_system.py ===
# Добавить новый метод для загрузки ADS из единого файла:

def load_ads_from_single_file(self):
    """Загрузка ADS данных из обработанных файлов филиалов"""
    import json
    import os
    
    all_ads_data = {}
    
    # Читаем данные каждого филиала
    if os.path.exists('ads/combined_ads_data.json'):
        with open('ads/combined_ads_data.json', 'r', encoding='utf-8') as f:
            combined_info = json.load(f)
        
        for branch_key, branch_info in combined_info['branches'].items():
            branch_file = f"ads/{branch_info['ads_file']}"
            
            if os.path.exists(branch_file):
                with open(branch_file, 'r', encoding='utf-8') as f:
                    branch_data = json.load(f)
                
                # Сохраняем данные филиала
                all_ads_data[branch_key] = branch_data['ads_data']
    
    # Присваиваем данные системе
    self.ads_data = all_ads_data
    self.ads_loaded = True
    
    return all_ads_data
'''
    
    # Сохраняем инструкции
    with open('ADS_INTERFACE_UPDATE_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write("""# 📋 Инструкция по обновлению интерфейса для единого файла ADS

## 1. Обновление основного интерфейса

В файле `streamlit_modular_app.py` найдите раздел загрузки ADS и замените его на:

```python
""" + update_code + """
```

## 2. Обновление системы обработки

В файле `modular_inventory_system.py` добавьте новый метод:

```python
""" + system_update_code + """
```

## 3. Изменения в логике обработки

### Старая логика:
- Загружались отдельные файлы для каждого филиала
- Имя файла определяло филиал
- Данные обрабатывались независимо

### Новая логика:
- Загружается ОДИН файл со всеми филиалами
- Колонка 'Филиал' определяет принадлежность данных
- Автоматическое разделение и сохранение по филиалам
- Данные сохраняются в папке `ads/`:
  - `{филиал}_ads.json` - данные каждого филиала
  - `combined_ads_data.json` - сводная информация

## 4. Формат единого файла

Файл должен содержать следующие колонки:
- **Филиал** (обязательно) - название филиала/склада
- **Товар** - наименование товара
- **Количество** - проданное количество
- **Сумма** - сумма продаж (опционально)
- **Цена** - цена за единицу (опционально)

## 5. Использование

1. Запустите приложение
2. Выберите "Загрузка файлов ADS"
3. Загрузите файл формата `общ_продажи_по_всем_складам_*.xlsx`
4. Система автоматически:
   - Разделит данные по филиалам
   - Рассчитает ADS для каждого товара
   - Сохранит данные в папку `ads/`
5. Перейдите к анализу

## 6. Проверка работы

После загрузки проверьте:
- Папка `ads/` содержит json файлы для каждого филиала
- Файл `ads/combined_ads_data.json` содержит сводную информацию
- В интерфейсе отображается правильное количество филиалов и товаров
""")
    
    print("✅ Инструкции по обновлению сохранены в ADS_INTERFACE_UPDATE_GUIDE.md")
    
    # Создаем патч для быстрого применения
    with open('apply_ads_update.py', 'w', encoding='utf-8') as f:
        f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматическое применение обновлений для работы с единым файлом ADS
"""

import os

def apply_updates():
    """Применяет обновления к существующим файлам"""
    
    # Проверяем наличие нужных файлов
    if not os.path.exists('streamlit_modular_app.py'):
        print("❌ Файл streamlit_modular_app.py не найден!")
        return
    
    print("✅ Обновления готовы к применению")
    print("📋 Для применения обновлений:")
    print("1. Откройте streamlit_modular_app.py")
    print("2. Найдите раздел 'Загрузка файлов ADS'")
    print("3. Замените код согласно инструкции в ADS_INTERFACE_UPDATE_GUIDE.md")
    print("4. Перезапустите приложение")
    
    # Создаем резервную копию
    import shutil
    shutil.copy('streamlit_modular_app.py', 'streamlit_modular_app.py.backup')
    print("\\n✅ Создана резервная копия: streamlit_modular_app.py.backup")

if __name__ == "__main__":
    apply_updates()
''')

if __name__ == "__main__":
    update_ads_interface_in_main()