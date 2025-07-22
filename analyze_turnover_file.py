import pandas as pd
import numpy as np

def analyze_turnover_file():
    file_path = '/mnt/f/Работа-Никита/Autosort_tovar/ОБОРАЧИВАЕМОСТЬ 10.07.2025.xlsx'
    
    # Читаем файл
    df = pd.read_excel(file_path)
    
    print('=== АНАЛИЗ ОБОРАЧИВАЕМОСТИ ТОВАРОВ ===')
    print(f'Общее количество записей: {len(df)}')
    
    # Очищаем данные - удаляем строку заголовков
    df_clean = df[df['Unnamed: 7'] != 'abc'].copy()
    
    # Конвертируем price в числовой формат
    df_clean['price_numeric'] = pd.to_numeric(df_clean['Unnamed: 6'], errors='coerce')
    
    # ABC анализ
    print('\n=== ABC АНАЛИЗ ТОВАРОВ ===')
    abc_analysis = df_clean['Unnamed: 7'].value_counts()
    abc_percent = (abc_analysis / abc_analysis.sum() * 100).round(2)
    for category, count in abc_analysis.items():
        print(f'Категория {category}: {count} товаров ({abc_percent[category]}%)')
    
    # Средняя цена по ABC категориям
    print('\n=== СРЕДНЯЯ ЦЕНА ПО ABC КАТЕГОРИЯМ ===')
    avg_price_by_abc = df_clean.groupby('Unnamed: 7')['price_numeric'].agg(['mean', 'count'])
    for category in avg_price_by_abc.index:
        avg_price = avg_price_by_abc.loc[category, 'mean']
        count = avg_price_by_abc.loc[category, 'count']
        if not np.isnan(avg_price):
            print(f'Категория {category}: средняя цена {avg_price:.2f} руб. (товаров с ценой: {count})')
    
    # Топ категорий
    print('\n=== ТОП-5 КАТЕГОРИЙ ТОВАРОВ ===')
    top_categories = df_clean['КАТЕГОРИЯ'].value_counts().head()
    for category, count in top_categories.items():
        print(f'{category}: {count} товаров')
    
    # Анализ по подкатегориям
    print('\n=== ТОП-10 ПОДКАТЕГОРИЙ ===')
    top_subcategories = df_clean['КАТ-2'].value_counts().head(10)
    for subcat, count in top_subcategories.items():
        if pd.notna(subcat):
            print(f'{subcat}: {count} товаров')
    
    # Анализ товаров категории A (самые важные)
    print('\n=== АНАЛИЗ ТОВАРОВ КАТЕГОРИИ A (ВЫСОКООБОРОТНЫЕ) ===')
    category_a = df_clean[df_clean['Unnamed: 7'] == 'A']
    if not category_a.empty:
        print(f'Товаров категории A: {len(category_a)}')
        print('Топ категории для товаров A:')
        for cat, count in category_a['КАТЕГОРИЯ'].value_counts().head().items():
            print(f'  {cat}: {count} товаров')
    
    return df_clean

if __name__ == '__main__':
    df_result = analyze_turnover_file()