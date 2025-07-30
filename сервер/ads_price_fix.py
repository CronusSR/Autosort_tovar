# ads_price_fix.py
"""
🔧 ИСПРАВЛЕНИЕ ЗАГРУЗКИ ADS С ЦЕНАМИ
Исправляет метод load_sales_file_updated для правильного извлечения цен из колонки 12
"""

import pandas as pd
import streamlit as st
import io
import types


def fix_ads_loading_with_prices(system):
    """
    ГЛАВНОЕ ИСПРАВЛЕНИЕ: Заменяет метод load_sales_file_updated для правильного извлечения цен
    """
    
    def load_sales_file_updated_with_prices(self, file_content) -> dict:
        """
        ИСПРАВЛЕННЫЙ метод загрузки ADS файла с извлечением цен из колонки 12 "Посл. закупка"
        """
        try:
            st.info("🔄 Обработка файла с извлечением цен из колонки 12 'Посл. закупка'...")
        
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        
            st.write(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # ТОЧНЫЕ параметры обработки (на основе анализа вашего кода)
            start_col_index = 12  # Колонка M (продажи)
            end_col_index = 28    # Колонка AB+1 (не включается)
            start_row = 3         # Строка 4 (индекс 3)
            nomenclature_col = 1  # Колонка B (номенклатура)
            price_col = 11        # 🔧 КЛЮЧЕВОЕ: Колонка 12 "Посл. закупка" (индекс 11)
            
            st.info(f"""
            📋 **Параметры обработки файла:**
            - Номенклатура: Колонка B (индекс {nomenclature_col})
            - **ЦЕНЫ: Колонка L (12) "Посл. закупка" (индекс {price_col})**
            - Данные продаж: колонки {start_col_index}:{end_col_index} (M:AB)
            - Начальная строка: {start_row+1}
            """)
            
            # Проверяем достаточность колонок
            if df.shape[1] <= max(end_col_index, price_col, nomenclature_col):
                return {
                    'success': False,
                    'error': f'Недостаточно колонок в файле. Найдено {df.shape[1]}, нужно минимум {max(end_col_index, price_col, nomenclature_col)+1}'
                }
            
            # Проверяем достаточность строк
            if df.shape[0] <= start_row:
                return {
                    'success': False,
                    'error': f'Недостаточно строк в файле. Найдено {df.shape[0]}, нужно минимум {start_row+1}'
                }
            
            # 🔧 ГЛАВНОЕ: Извлекаем данные по товарам с ЦЕНАМИ
            sales_data_list = []
            prices_found = 0
            prices_processed = 0
            
            # Обрабатываем строки начиная с 4й (индекс 3)
            for idx in range(start_row, df.shape[0]):
                row = df.iloc[idx]
                
                # Получаем номенклатуру из колонки B
                nomenclature = row.iloc[nomenclature_col] if nomenclature_col < len(row) else None
                if pd.isna(nomenclature) or str(nomenclature).strip() == '':
                    continue
                
                item_name = str(nomenclature).strip()
                
                # 🔧 КЛЮЧЕВОЕ: Извлекаем ЦЕНУ из колонки 12 "Посл. закупка"
                try:
                    raw_price = row.iloc[price_col] if price_col < len(row) else None
                    if pd.notna(raw_price) and str(raw_price).strip() != '':
                        item_price = float(raw_price)
                        if item_price > 0:
                            prices_found += 1
                    else:
                        item_price = 0.0
                    prices_processed += 1
                except (ValueError, TypeError, IndexError):
                    item_price = 0.0
                    prices_processed += 1
                
                # Извлекаем данные продаж из колонок M:AB
                row_sales_data = df.iloc[idx, start_col_index:end_col_index].copy()
                row_sales_numeric = pd.to_numeric(row_sales_data, errors='coerce').fillna(0)
                
                # Формула ADS: среднее значение / 30.5
                average_value = row_sales_numeric.mean()
                ads_value = average_value / 30.5
                
                sales_data_list.append({
                    'номенклатура': item_name,
                    'ads': ads_value,
                    'average_value': average_value,
                    'total_sales': row_sales_numeric.sum(),
                    'monthly_data': row_sales_numeric.tolist(),
                    'last_purchase_price': float(item_price)  # 🔧 КЛЮЧЕВОЕ: Добавляем цену
                })
            
            # Создаем DataFrame
            ads_df = pd.DataFrame(sales_data_list)
            
            # Исключаем последнюю строку (как в оригинальном коде)
            if len(ads_df) > 1:
                ads_df = ads_df.iloc[:-1].copy()
            
            # 🔧 ВАЖНО: Сохраняем результаты в системе
            self.sales_data = ads_df  # Для топ товаров
            self.calculated_ads = ads_df[['номенклатура', 'ads', 'average_value', 'total_sales', 'last_purchase_price']].copy()
            
            # Статистика по ценам
            st.success(f"""
            ✅ **Обработка завершена с ЦЕНАМИ:**
            - Всего товаров: {len(ads_df)}
            - С положительным ADS: {len(ads_df[ads_df['ads'] > 0])}
            - **С ценами: {prices_found} из {prices_processed}**
            - **Покрытие ценами: {(prices_found/prices_processed*100):.1f}%**
            - Общий ADS: {ads_df['ads'].sum():.2f}
            """)
            
            # Показываем примеры товаров с ценами
            if prices_found > 0:
                st.success(f"💰 **Примеры товаров с ценами:**")
                with_prices = ads_df[ads_df['last_purchase_price'] > 0].head(3)
                for i, (_, row) in enumerate(with_prices.iterrows(), 1):
                    st.write(f"  {i}. {row['номенклатура'][:40]} | ADS: {row['ads']:.4f} | Цена: {row['last_purchase_price']:.2f} ₽")
            else:
                st.warning(f"""
                ⚠️ **ЦЕНЫ НЕ НАЙДЕНЫ!**
                
                **Проверьте:**
                1. В колонке L (12) должны быть цены "Посл. закупка"
                2. Цены должны быть больше 0
                3. Колонка не должна быть пустой
                
                **Текущее состояние колонки 12:**
                - Обработано строк с ценами: {prices_processed}
                - Найдено цен > 0: {prices_found}
                """)
            
            return {
                'success': True,
                'total_items': len(ads_df),
                'nomenclature_column': 'B',
                'price_column': 'L (12) - Посл. закупка',
                'calculation_method': 'average_monthly_divided_by_30_with_prices',
                'total_ads': ads_df['ads'].sum(),
                'average_ads': ads_df['ads'].mean(),
                'items_with_positive_ads': len(ads_df[ads_df['ads'] > 0]),
                'prices_extracted': True,
                'prices_found': prices_found,
                'prices_processed': prices_processed,
                'price_coverage_percentage': (prices_found/prices_processed*100) if prices_processed > 0 else 0,
                'total_inventory_value': float((ads_df['ads'] * 30 * ads_df['last_purchase_price']).sum())
            }
            
        except Exception as e:
            st.error(f"❌ Ошибка обработки файла: {str(e)}")
            import traceback
            st.exception(e)
            return {'success': False, 'error': f"Ошибка загрузки файла: {str(e)}"}
    
    # 🔧 ПРИМЕНЯЕМ ИСПРАВЛЕНИЕ: Заменяем метод в системе
    system.load_sales_file_updated = types.MethodType(load_sales_file_updated_with_prices, system)
    
    st.success("✅ Метод load_sales_file_updated исправлен для работы с ценами!")
    st.info("""
    🔧 **Что исправлено:**
    - Правильное извлечение цен из колонки 12 "Посл. закупка"
    - Добавление колонки 'last_purchase_price' в ADS данные
    - Детальная статистика по ценам
    - Проверка и валидация ценовых данных
    """)
    
    return True


def check_ads_prices_after_fix(system):
    """
    Проверяет наличие цен в ADS данных после исправления
    """
    
    st.subheader("🔍 Проверка цен в ADS данных")
    
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.warning("⚠️ ADS не рассчитан. Сначала загрузите файл продаж.")
        return False
    
    ads_data = system.calculated_ads
    
    # Проверяем наличие колонки цен
    has_price_column = 'last_purchase_price' in ads_data.columns
    
    if has_price_column:
        total_items = len(ads_data)
        items_with_price = len(ads_data[ads_data['last_purchase_price'] > 0])
        items_without_price = total_items - items_with_price
        
        # Показываем результаты
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего товаров", total_items)
        with col2:
            st.metric("С ценами", items_with_price)
        with col3:
            st.metric("Без цен", items_without_price)
        with col4:
            coverage = (items_with_price/total_items*100) if total_items > 0 else 0
            st.metric("Покрытие", f"{coverage:.1f}%")
        
        if items_with_price > 0:
            valid_prices = ads_data[ads_data['last_purchase_price'] > 0]['last_purchase_price']
            
            st.success(f"""
            ✅ **Цены найдены в ADS данных!**
            
            **Статистика цен:**
            - Средняя цена: {valid_prices.mean():.2f} ₽
            - Минимальная цена: {valid_prices.min():.2f} ₽
            - Максимальная цена: {valid_prices.max():.2f} ₽
            - Общая стоимость месячных продаж: {(ads_data['ads'] * 30 * ads_data['last_purchase_price']).sum():,.0f} ₽
            """)
            
            # Показываем примеры
            with st.expander("💰 Примеры товаров с ценами"):
                top_items = ads_data[ads_data['last_purchase_price'] > 0].nlargest(5, 'last_purchase_price')
                for i, (_, row) in enumerate(top_items.iterrows(), 1):
                    st.write(f"**{i}.** {row['номенклатура'][:50]}")
                    st.write(f"   💰 Цена: {row['last_purchase_price']:,.2f} ₽ | ADS: {row['ads']:.4f}")
            
            return True
        else:
            st.error("""
            ❌ **Колонка 'last_purchase_price' найдена, но ВСЕ цены равны 0!**
            
            **Возможные причины:**
            1. В колонке 12 "Посл. закупка" нет данных
            2. Все цены в файле равны 0
            3. Данные в колонке не числовые
            
            **Решение:**
            1. Проверьте колонку L (12) в исходном Excel файле
            2. Убедитесь что там есть цены больше 0
            3. Перезагрузите файл продаж
            """)
            return False
    else:
        st.error("""
        ❌ **Колонка 'last_purchase_price' НЕ найдена в ADS данных!**
        
        **Это означает что метод load_sales_file_updated не был исправлен.**
        
        **Найденные колонки в ADS:**
        """ + str(list(ads_data.columns)))
        
        st.error("""
        **Для исправления:**
        1. Примените исправление: `fix_ads_loading_with_prices(system)`
        2. Перезагрузите файл продаж в разделе "ADS расчет"
        3. Убедитесь что в файле есть колонка 12 "Посл. закупка" с ценами
        """)
        return False


def create_ads_price_fix_page():
    """
    Создает страницу для исправления ADS с ценами
    """
    
    def ads_price_fix_page(system):
        """
        Страница исправления загрузки ADS с ценами
        """
        
        st.header("🔧 Исправление ADS для работы с ценами")
        st.caption("Исправляет метод загрузки файла продаж для извлечения цен из колонки 12")
        
        # Проверяем текущее состояние
        st.subheader("📊 Текущее состояние системы")
        
        has_ads = hasattr(system, 'calculated_ads') and system.calculated_ads is not None
        has_prices_in_ads = False
        
        if has_ads:
            st.success(f"✅ ADS рассчитан: {len(system.calculated_ads)} товаров")
            has_prices_in_ads = 'last_purchase_price' in system.calculated_ads.columns
            
            if has_prices_in_ads:
                items_with_price = len(system.calculated_ads[system.calculated_ads['last_purchase_price'] > 0])
                st.success(f"✅ Цены найдены: {items_with_price} товаров с ценами")
            else:
                st.error("❌ Цены в ADS данных НЕ найдены")
        else:
            st.warning("⚠️ ADS не рассчитан")
        
        # Кнопка исправления
        st.subheader("🔧 Применить исправление")
        
        if st.button("🚀 Исправить метод загрузки ADS для работы с ценами", type="primary"):
            
            with st.spinner("Применяем исправление метода load_sales_file_updated..."):
                success = fix_ads_loading_with_prices(system)
            
            if success:
                st.success("✅ Исправление применено! Теперь перезагрузите файл продаж в разделе 'ADS расчет'")
                
                st.info("""
                📋 **Следующие шаги:**
                
                1. **Перейдите в раздел "ADS расчет"**
                2. **Загрузите файл продаж заново**
                3. **Убедитесь что в файле есть колонка L (12) "Посл. закупка" с ценами**
                4. **Проверьте результат - должны появиться цены в ADS**
                5. **Используйте анализ складов с ценами**
                """)
            else:
                st.error("❌ Не удалось применить исправление")
        
        # Проверка цен после исправления
        if has_ads:
            st.subheader("🔍 Проверка цен в текущих ADS данных")
            check_ads_prices_after_fix(system)
        
        # Инструкции по структуре файла
        st.subheader("📋 Требования к структуре файла продаж")
        
        st.info("""
        **Правильная структура файла продаж:**
        
        ```
        | A   | B            | ... | L (12)      | M   | N   | ... | AB  |
        |-----|--------------|-----|-------------|-----|-----|-----|-----|
        | Код | Номенклатура | ... | Посл.закупка| Янв | Фев | ... | Дек |
        | 001 | Товар 1      | ... | 150.50      | 10  | 15  | ... | 20  |
        | 002 | Товар 2      | ... | 89.30       | 5   | 8   | ... | 12  |
        ```
        
        **Ключевые требования:**
        - Номенклатура в колонке **B**
        - Цены в колонке **L (12)** с названием "Посл. закупка"
        - Данные продаж в колонках **M:AB**
        - Данные начинаются с **4-й строки**
        - Цены должны быть **больше 0**
        """)
    
    return ads_price_fix_page


# Главная функция для быстрого применения
def quick_ads_price_fix(system):
    """
    Быстрое исправление ADS для работы с ценами
    """
    
    try:
        # Применяем исправление
        success = fix_ads_loading_with_prices(system)
        
        if success:
            # Создаем и показываем страницу
            ads_page = create_ads_price_fix_page()
            ads_page(system)
        
        return success
        
    except Exception as e:
        st.error(f"❌ Ошибка исправления ADS: {str(e)}")
        return False


if __name__ == "__main__":
    print("🔧 Исправление загрузки ADS с ценами")
    print("Исправляет метод load_sales_file_updated для извлечения цен из колонки 12")
    print("\nДля использования:")
    print("from ads_price_fix import quick_ads_price_fix")
    print("quick_ads_price_fix(system)")
    print("\nИли в разделе анализа складов:")
    print("from ads_price_fix import fix_ads_loading_with_prices")
    print("fix_ads_loading_with_prices(system)")