# quick_fix_method_missing.py
"""
БЫСТРОЕ ИСПРАВЛЕНИЕ отсутствующего метода analyze_warehouse_stock_with_details
ДОБАВЬТЕ этот код В ФУНКЦИЮ warehouse_analysis_page ПЕРЕД ВЫЗОВОМ АНАЛИЗА
"""

# 🚨 ИСПРАВЛЕНИЕ ОТСУТСТВУЮЩЕГО МЕТОДА - добавить перед кнопкой анализа:

# Проверяем и добавляем отсутствующий метод
if not hasattr(system, 'analyze_warehouse_stock_with_details'):
    
    def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city, min_days=10, max_days=50):
        """Простой анализ складов с деталями"""
        
        try:
            # Если нет анализатора, создаем его
            if not hasattr(system, 'warehouse_analyzer'):
                from restore_detailed_warehouse_analysis import DetailedWarehouseAnalyzer
                system.warehouse_analyzer = DetailedWarehouseAnalyzer()
            
            # Запускаем детальный анализ
            analysis = system.warehouse_analyzer.analyze_warehouse_stock_detailed(
                remains_df, ads_data, store_ads_by_city, min_days, max_days
            )
            
            if analysis:
                recommendations = system.warehouse_analyzer.get_warehouse_recommendations()
                return analysis, recommendations
            
            return None, None
            
        except Exception as e:
            st.error(f"❌ Ошибка анализа: {str(e)}")
            return None, None
    
    # Добавляем метод к системе
    system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
    st.info("🔧 Метод анализа добавлен к системе")

"""
ГДЕ ДОБАВИТЬ:

В функции warehouse_analysis_page, найдите строку:
    if st.button("🔍 Запустить детальный анализ складов", type="primary"):

И ПЕРЕД НЕЙ добавьте весь код выше.

ПРИМЕР:

    # ... код загрузки файла ...
    
    # 🚨 ДОБАВИТЬ ЗДЕСЬ КОД ИСПРАВЛЕНИЯ
    if not hasattr(system, 'analyze_warehouse_stock_with_details'):
        def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city, min_days=10, max_days=50):
            # ... код функции ...
        system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
        st.info("🔧 Метод анализа добавлен к системе")
    
    # Кнопка детального анализа
    if st.button("🔍 Запустить детальный анализ складов", type="primary"):
        # ... остальной код ...
"""