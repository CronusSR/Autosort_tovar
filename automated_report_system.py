#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматизированная система ежедневных отчетов
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
import schedule
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from jinja2 import Template
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_reports.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutomatedReportSystem:
    """Система автоматизированной генерации отчетов"""
    
    def __init__(self, config_file="report_config.json"):
        self.webhook_dir = Path('./webhook_uploads')
        self.reports_dir = Path('./automated_reports')
        self.reports_dir.mkdir(exist_ok=True)
        
        # Загружаем конфигурацию
        self.config = self.load_config(config_file)
        
        # Иерархия складов (из исходного кода)
        self.WAREHOUSE_HIERARCHY = {
            "hub": "База Склад Фурнитура Комплект",
            "level2_warehouses": {
                "Казыбаева Склад Фурнитура TRADE": ["ТД Казыбаева ФУРНИТУРА магазин"],
                "склад фурнитура № 1": ["Магазин фурнитуры"],
                "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"": ["6 Склад фурнитуры \"Овощная база\" Магазин продажи"]
            },
            "direct_stores_from_hub": [
                "Барыс Склад Фурнитура TRADE",
                "АО Склад Фурнитура TRADE"
            ]
        }
    
    def load_config(self, config_file):
        """Загружает конфигурацию системы"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": []
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_ids": []
            },
            "schedule": {
                "time": "09:00",
                "enabled": True
            },
            "analysis_settings": {
                "hub": {"min": 60, "max": 180},
                "warehouse": {"min": 30, "max": 90},
                "store": {"min": 14, "max": 45}
            }
        }
        
        try:
            if Path(config_file).exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Объединяем с дефолтными значениями
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # Создаем файл конфигурации по умолчанию
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                logger.info(f"Создан файл конфигурации: {config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            return default_config
    
    def get_latest_files(self):
        """Получает последние файлы данных"""
        files = {'sales': None, 'stock': None}
        
        if not self.webhook_dir.exists():
            return files
        
        # Ищем файлы за последние 2 дня
        cutoff_date = datetime.now() - timedelta(days=2)
        
        sales_files = [f for f in self.webhook_dir.glob('sales_*.json') 
                      if datetime.fromtimestamp(f.stat().st_mtime) > cutoff_date]
        stock_files = [f for f in self.webhook_dir.glob('stock_*.json')
                      if datetime.fromtimestamp(f.stat().st_mtime) > cutoff_date]
        
        if sales_files:
            files['sales'] = max(sales_files, key=lambda x: x.stat().st_mtime)
        
        if stock_files:
            files['stock'] = max(stock_files, key=lambda x: x.stat().st_mtime)
        
        return files
    
    def parse_data(self, files):
        """Парсит данные из файлов"""
        try:
            from enhanced_data_parser import enhanced_parser
            
            if files['sales']:
                with open(files['sales'], 'r', encoding='utf-8') as f:
                    sales_data = json.load(f)
                sales_df, period_days = enhanced_parser.parse_new_sales_data(sales_data)
            else:
                sales_df, period_days = pd.DataFrame(), 30.5
            
            if files['stock']:
                with open(files['stock'], 'r', encoding='utf-8') as f:
                    stock_data = json.load(f)
                stock_df = enhanced_parser.parse_stock_data(stock_data)
            else:
                stock_df = pd.DataFrame()
            
            return sales_df, stock_df, period_days
            
        except Exception as e:
            logger.error(f"Ошибка парсинга данных: {e}")
            return pd.DataFrame(), pd.DataFrame(), 30.5
    
    def generate_movement_recommendations(self, stock_df, sales_df, period_days):
        """Генерирует рекомендации по перемещению (упрощенная версия)"""
        recommendations = []
        
        if stock_df.empty or sales_df.empty:
            return recommendations
        
        try:
            # Объединяем данные по артикулам и филиалам
            for article in stock_df['article'].unique():
                article_stock = stock_df[stock_df['article'] == article]
                article_sales = sales_df[sales_df['article'] == article]
                
                if article_sales.empty:
                    continue
                
                for _, stock_row in article_stock.iterrows():
                    branch = stock_row['branch']
                    branch_type = self.get_branch_type(branch)
                    
                    # Настройки для типа филиала
                    settings = self.config['analysis_settings'].get(branch_type, {'min': 30, 'max': 90})
                    
                    # Находим продажи этого товара в этом филиале
                    branch_sales = article_sales[article_sales['branch'] == branch]['cost'].sum()
                    
                    if branch_sales > 0:
                        # Рассчитываем оборачиваемость
                        turnover_days = int((stock_row['cost'] / branch_sales) * period_days)
                        
                        # Проверяем нужно ли перемещение
                        if turnover_days > settings['max']:
                            # Избыток - нужно отправить
                            excess_days = turnover_days - settings['max']
                            quantity_to_move = int(stock_row['quantity'] * 0.3)  # 30% от избытка
                            
                            if quantity_to_move > 0:
                                recommendations.append({
                                    'from_branch': branch,
                                    'to_branch': self.find_best_destination(branch, article, stock_df, sales_df),
                                    'article': article,
                                    'product': stock_row['product'],
                                    'quantity': quantity_to_move,
                                    'reason': f"Избыток на {excess_days} дней, оборачиваемость {turnover_days} дней",
                                    'priority': 'high' if excess_days > 100 else 'medium',
                                    'current_turnover': turnover_days
                                })
                        
                        elif turnover_days < settings['min']:
                            # Недостаток - нужно получить
                            shortage_days = settings['min'] - turnover_days
                            
                            recommendations.append({
                                'from_branch': self.find_best_source(branch, article, stock_df, sales_df),
                                'to_branch': branch,
                                'article': article,
                                'product': stock_row['product'],
                                'quantity': int(stock_row['quantity'] * 0.5),  # Увеличиваем на 50%
                                'reason': f"Недостаток на {shortage_days} дней, оборачиваемость {turnover_days} дней",
                                'priority': 'high' if shortage_days > 10 else 'medium',
                                'current_turnover': turnover_days
                            })
            
            return recommendations[:100]  # Лимитируем количество
            
        except Exception as e:
            logger.error(f"Ошибка генерации рекомендаций: {e}")
            return []
    
    def get_branch_type(self, branch_name):
        """Определяет тип филиала"""
        if branch_name == self.WAREHOUSE_HIERARCHY["hub"]:
            return "hub"
        elif branch_name in self.WAREHOUSE_HIERARCHY["level2_warehouses"]:
            return "warehouse"
        elif branch_name in self.WAREHOUSE_HIERARCHY["direct_stores_from_hub"]:
            return "store"
        else:
            for warehouse, stores in self.WAREHOUSE_HIERARCHY["level2_warehouses"].items():
                if branch_name in stores:
                    return "store"
        return "unknown"
    
    def find_best_destination(self, from_branch, article, stock_df, sales_df):
        """Находит лучший пункт назначения для товара"""
        # Упрощенно - отправляем в хаб
        return self.WAREHOUSE_HIERARCHY["hub"]
    
    def find_best_source(self, to_branch, article, stock_df, sales_df):
        """Находит лучший источник товара"""
        # Упрощенно - берем из хаба
        return self.WAREHOUSE_HIERARCHY["hub"]
    
    def calculate_abc_analysis(self, sales_df, stock_df, period_days):
        """Рассчитывает ABC анализ по категориям"""
        if sales_df.empty or stock_df.empty:
            return []
        
        try:
            # Извлекаем категории
            def extract_main_category(path):
                if pd.isna(path) or path == "":
                    return "Без категории"
                parts = str(path).split('/')
                return parts[0] if parts and parts[0] else "Без категории"
            
            stock_df['category'] = stock_df['category_path'].apply(extract_main_category)
            sales_df['category'] = sales_df['category_path'].apply(extract_main_category)
            
            abc_results = []
            
            for category in sorted(stock_df['category'].unique()):
                cat_sales = sales_df[sales_df['category'] == category]['cost'].sum()
                cat_stock = stock_df[stock_df['category'] == category]['cost'].sum()
                
                if cat_sales > 0:
                    turnover = int((cat_stock / cat_sales) * period_days)
                else:
                    turnover = 999
                
                # ABC классификация
                if turnover <= 90:
                    abc_class = 'A'
                elif turnover <= 180:
                    abc_class = 'B'
                else:
                    abc_class = 'C'
                
                abc_results.append({
                    'category': category,
                    'sales': cat_sales,
                    'stock': cat_stock,
                    'turnover': turnover,
                    'abc_class': abc_class
                })
            
            return sorted(abc_results, key=lambda x: x['turnover'])
            
        except Exception as e:
            logger.error(f"Ошибка ABC анализа: {e}")
            return []
    
    def generate_full_report(self):
        """Генерирует полный отчет"""
        logger.info("Начинаю генерацию полного отчета...")
        
        # Получаем файлы
        files = self.get_latest_files()
        
        if not files['sales'] or not files['stock']:
            logger.warning("Недостаточно файлов для создания отчета")
            return None
        
        # Парсим данные
        sales_df, stock_df, period_days = self.parse_data(files)
        
        if sales_df.empty or stock_df.empty:
            logger.warning("Нет данных для анализа")
            return None
        
        # Генерируем анализы
        recommendations = self.generate_movement_recommendations(stock_df, sales_df, period_days)
        abc_analysis = self.calculate_abc_analysis(sales_df, stock_df, period_days)
        
        # Создаем отчет
        report = {
            'timestamp': datetime.now().isoformat(),
            'period_days': period_days,
            'files_used': {
                'sales': files['sales'].name if files['sales'] else None,
                'stock': files['stock'].name if files['stock'] else None
            },
            'summary': {
                'total_branches': stock_df['branch'].nunique(),
                'total_products': stock_df['article'].nunique(),
                'total_sales': sales_df['cost'].sum(),
                'total_stock': stock_df['cost'].sum(),
                'recommendations_count': len(recommendations),
                'categories_count': len(abc_analysis)
            },
            'recommendations': recommendations,
            'abc_analysis': abc_analysis,
            'branch_stats': self.calculate_branch_stats(sales_df, stock_df, period_days)
        }
        
        # Сохраняем отчет
        report_file = self.save_report(report)
        
        # Отправляем отчет
        self.send_report(report, report_file)
        
        logger.info(f"Отчет сгенерирован: {report_file}")
        return report_file
    
    def calculate_branch_stats(self, sales_df, stock_df, period_days):
        """Рассчитывает статистику по филиалам"""
        branch_stats = []
        
        for branch in stock_df['branch'].unique():
            branch_sales = sales_df[sales_df['branch'] == branch]['cost'].sum()
            branch_stock = stock_df[stock_df['branch'] == branch]['cost'].sum()
            
            if branch_sales > 0:
                turnover = int((branch_stock / branch_sales) * period_days)
            else:
                turnover = 999
            
            branch_stats.append({
                'branch': branch,
                'type': self.get_branch_type(branch),
                'sales': branch_sales,
                'stock': branch_stock,
                'turnover': turnover,
                'products_count': stock_df[stock_df['branch'] == branch]['article'].nunique()
            })
        
        return sorted(branch_stats, key=lambda x: x['turnover'])
    
    def save_report(self, report):
        """Сохраняет отчет в файл"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON отчет
        json_file = self.reports_dir / f"report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Excel отчет
        excel_file = self.reports_dir / f"report_{timestamp}.xlsx"
        self.create_excel_report(report, excel_file)
        
        return excel_file
    
    def create_excel_report(self, report, excel_file):
        """Создает Excel отчет"""
        try:
            with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                # Сводная информация
                summary_df = pd.DataFrame([report['summary']]).T
                summary_df.columns = ['Значение']
                summary_df.to_excel(writer, sheet_name='Сводка')
                
                # Рекомендации
                if report['recommendations']:
                    rec_df = pd.DataFrame(report['recommendations'])
                    rec_df.to_excel(writer, sheet_name='Рекомендации', index=False)
                
                # ABC анализ
                if report['abc_analysis']:
                    abc_df = pd.DataFrame(report['abc_analysis'])
                    abc_df.to_excel(writer, sheet_name='ABC Анализ', index=False)
                
                # Статистика по филиалам
                if report['branch_stats']:
                    branch_df = pd.DataFrame(report['branch_stats'])
                    branch_df.to_excel(writer, sheet_name='Статистика филиалов', index=False)
                
        except Exception as e:
            logger.error(f"Ошибка создания Excel отчета: {e}")
    
    def send_report(self, report, report_file):
        """Отправляет отчет по настроенным каналам"""
        try:
            # Email
            if self.config['email']['enabled'] and self.config['email']['recipients']:
                self.send_email_report(report, report_file)
            
            # Telegram
            if self.config['telegram']['enabled'] and self.config['telegram']['chat_ids']:
                self.send_telegram_report(report, report_file)
                
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
    
    def send_email_report(self, report, report_file):
        """Отправляет отчет по email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['username']
            msg['To'] = ', '.join(self.config['email']['recipients'])
            msg['Subject'] = f"Автоматический отчет по складам - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Текст письма
            body = self.create_email_body(report)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Прикрепляем Excel файл
            if report_file.exists():
                with open(report_file, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {report_file.name}'
                )
                msg.attach(part)
            
            # Отправляем
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['username'], self.config['email']['password'])
            server.sendmail(msg['From'], self.config['email']['recipients'], msg.as_string())
            server.quit()
            
            logger.info("Email отчет отправлен")
            
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")
    
    def create_email_body(self, report):
        """Создает тело email сообщения"""
        template = """
        <h2>📊 Автоматический отчет по складам</h2>
        <p><strong>Дата:</strong> {{ timestamp }}</p>
        <p><strong>Период анализа:</strong> {{ period_days }} дней</p>
        
        <h3>📈 Основные показатели</h3>
        <ul>
            <li>Филиалов: {{ summary.total_branches }}</li>
            <li>Товаров: {{ summary.total_products }}</li>
            <li>Общие продажи: {{ "{:,.0f}".format(summary.total_sales) }}</li>
            <li>Общие остатки: {{ "{:,.0f}".format(summary.total_stock) }}</li>
            <li>Рекомендаций: {{ summary.recommendations_count }}</li>
        </ul>
        
        <h3>🚨 Приоритетные рекомендации</h3>
        <ul>
        {% for rec in recommendations[:10] %}
            <li><strong>{{ rec.from_branch }}</strong> → <strong>{{ rec.to_branch }}</strong>: 
                {{ rec.product }} ({{ rec.quantity }} шт.) - {{ rec.reason }}</li>
        {% endfor %}
        </ul>
        
        <h3>📊 ABC Анализ (топ категории)</h3>
        <ul>
        {% for abc in abc_analysis[:5] %}
            <li><strong>{{ abc.category }}</strong> (класс {{ abc.abc_class }}): 
                Оборачиваемость {{ abc.turnover }} дней</li>
        {% endfor %}
        </ul>
        
        <p><em>Детальный отчет во вложенном Excel файле.</em></p>
        """
        
        tmpl = Template(template)
        return tmpl.render(**report)
    
    def send_telegram_report(self, report, report_file):
        """Отправляет отчет в Telegram"""
        try:
            bot_token = self.config['telegram']['bot_token']
            
            # Текстовое сообщение
            message = f"""
🤖 **Автоматический отчет по складам**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

📈 **Основные показатели:**
• Филиалов: {report['summary']['total_branches']}
• Товаров: {report['summary']['total_products']:,}
• Продажи: {report['summary']['total_sales']:,.0f}
• Остатки: {report['summary']['total_stock']:,.0f}
• Рекомендаций: {report['summary']['recommendations_count']}

🚨 **Приоритетные перемещения:**
"""
            
            # Добавляем топ рекомендации
            for rec in report['recommendations'][:5]:
                message += f"• {rec['from_branch']} → {rec['to_branch']}: {rec['quantity']} шт.\n"
            
            # Отправляем сообщение в каждый чат
            for chat_id in self.config['telegram']['chat_ids']:
                # Текст
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
                requests.post(url, data=data)
                
                # Файл (если есть)
                if report_file.exists():
                    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                    with open(report_file, 'rb') as f:
                        files = {'document': f}
                        data = {'chat_id': chat_id}
                        requests.post(url, data=data, files=files)
            
            logger.info("Telegram отчет отправлен")
            
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
    
    def start_scheduler(self):
        """Запускает планировщик"""
        if self.config['schedule']['enabled']:
            schedule_time = self.config['schedule']['time']
            schedule.every().day.at(schedule_time).do(self.generate_full_report)
            logger.info(f"Планировщик запущен: отчеты каждый день в {schedule_time}")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту

def main():
    """Основная функция"""
    system = AutomatedReportSystem()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'generate':
            # Создать отчет сейчас
            system.generate_full_report()
        elif sys.argv[1] == 'schedule':
            # Запустить планировщик
            system.start_scheduler()
        else:
            print("Использование: python automated_report_system.py [generate|schedule]")
    else:
        print("Создание тестового отчета...")
        system.generate_full_report()

if __name__ == "__main__":
    main()