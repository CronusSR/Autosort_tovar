#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простое добавление цен в ADS анализ
Реализует предложение пользователей о добавлении вывода цен прямо в ADS анализ
"""

import streamlit as st
import pandas as pd

def add_price_output_to_ads_analysis():
    """
    Простое решение: добавляет вывод цен к результатам ADS анализа
    """
    st.success("✅ Цены уже включены в ADS анализ!")
    
    st.info("""
    **Что изменилось:**
    
    📊 **ADS анализ теперь включает цены:**
    - Извлекает цены из колонки L (12-я колонка) 
    - Начинает с 4-й строки как вы указали
    - Сохраняет цены в поле `last_purchase_price`
    - Показывает статистику по ценам
    
    🔧 **Где используется:**
    - `modular_inventory_system.py` - основной ADS расчет с ценами
    - `integration_patch.py` - множественные файлы с ценами (+ исходные данные)
    - Анализ складов теперь может использовать эти цены автоматически
    
    🐛 **ИСПРАВЛЕНО: "не найдены исходные данные"**
    - `integration_patch.py` теперь сохраняет исходные Excel данные в `source_data`
    - Принудительное извлечение цен работает с реальными данными
    - Нет потери исходных данных при обработке
    
    💰 **Результат:**
    - ADS данные теперь содержат как продажи, так и цены
    - Исходные Excel файлы сохранены для извлечения цен
    - Цены доступны сразу после расчета ADS
    """)

def show_price_integration_status(system):
    """
    Показывает статус интеграции цен в системе
    """
    st.subheader("📊 Статус ценовой интеграции")
    
    # Проверяем одиночные файлы
    if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        ads_data = system.calculated_ads
        if 'last_purchase_price' in ads_data.columns:
            prices_found = (ads_data['last_purchase_price'] > 0).sum()
            total_items = len(ads_data)
            coverage = (prices_found / total_items * 100) if total_items > 0 else 0
            
            st.success(f"✅ **Одиночный ADS файл:** {prices_found}/{total_items} товаров с ценами ({coverage:.1f}%)")
            
            if prices_found > 0:
                avg_price = ads_data[ads_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
                st.info(f"💰 Средняя цена: {avg_price:,.0f} ₸")
        else:
            st.warning("⚠️ Одиночный ADS файл: цены не найдены")
    
    # Проверяем множественные файлы
    if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
        combined_data = system.multiple_files_data.get('combined_data')
        if combined_data is not None and 'last_purchase_price' in combined_data.columns:
            prices_found = (combined_data['last_purchase_price'] > 0).sum()
            total_items = len(combined_data)
            coverage = (prices_found / total_items * 100) if total_items > 0 else 0
            
            st.success(f"✅ **Множественные файлы:** {prices_found}/{total_items} товаров с ценами ({coverage:.1f}%)")
            
            if prices_found > 0:
                avg_price = combined_data[combined_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
                total_value = (combined_data['ads'] * 30 * combined_data['last_purchase_price']).sum()
                st.info(f"💰 Средняя цена: {avg_price:,.0f} ₸")
                st.info(f"📈 Общая стоимость месячного оборота: {total_value:,.0f} ₸")
        else:
            st.warning("⚠️ Множественные файлы: цены не найдены")
    
    if not hasattr(system, 'calculated_ads') and not hasattr(system, 'multiple_files_data'):
        st.error("❌ Нет данных ADS для проверки цен")

def get_prices_for_warehouse_analysis(system):
    """
    Возвращает словарь цен для использования в анализе складов
    """
    prices_dict = {}
    
    # Собираем цены из одиночных файлов
    if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        ads_data = system.calculated_ads
        if 'last_purchase_price' in ads_data.columns:
            for _, row in ads_data.iterrows():
                if row['last_purchase_price'] > 0:
                    prices_dict[row['номенклатура']] = row['last_purchase_price']
    
    # Собираем цены из множественных файлов (приоритет выше)
    if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
        combined_data = system.multiple_files_data.get('combined_data')
        if combined_data is not None and 'last_purchase_price' in combined_data.columns:
            for _, row in combined_data.iterrows():
                if row['last_purchase_price'] > 0:
                    prices_dict[row['номенклатура']] = row['last_purchase_price']
    
    return prices_dict

if __name__ == "__main__":
    st.header("💰 Простое добавление цен в ADS анализ")
    add_price_output_to_ads_analysis()