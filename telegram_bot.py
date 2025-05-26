#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновленный Telegram бот для системы автоматизации товарных запасов v2.0
С поддержкой ABC анализа и полной логики Саната
"""

import logging
import os
import io
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from excel_processor_v2 import ExcelDataProcessorV2
from inventory_system_v2 import InventoryAutomationSystemV2
import plotly.express as px
import plotly.graph_objects as go
import tempfile

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

class InventoryBotV2:
    """Обновленный класс Telegram бота с ABC анализом"""
    
    def __init__(self):
        self.user_systems = {}  # Хранилище систем для каждого пользователя
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_id = update.effective_user.id
        
        # Инициализируем обновленную систему
        self.user_systems[user_id] = InventoryAutomationSystemV2()
        
        welcome_text = """
🤖 **Система автоматизации товарных запасов v2.0**

Привет! Я обновленный помощник для автоматизации управления товарными запасами по логике Саната.

🆕 **Новые возможности v2.0:**
🔤 ABC анализ по категориям
📊 Парето-анализ товаров  
🎯 Умное распределение полок
📈 Расширенная аналитика
🚛 Учет транзитного времени
✅ Фильтрация активного ассортимента

**Что я умею:**
📊 Анализировать категории товаров с ABC
📋 Формировать заказы по полной логике Саната
📤 Экспортировать расширенные отчеты
⚙️ Учитывать все параметры из детализации
🔍 Контролировать качество данных

**Как начать:**
1. 📁 Отправьте основной Excel файл
2. 🔤 Отправьте файл для ABC анализа  
3. ⚙️ Настройте параметры расчета
4. 📋 Получите готовые заказы с аналитикой

Отправьте /help для подробной инструкции.
        """
        
        keyboard = [
            [InlineKeyboardButton("📁 Загрузить основные данные", callback_data='upload_main')],
            [InlineKeyboardButton("🔤 Загрузить ABC данные", callback_data='upload_abc')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
📖 **Подробная инструкция v2.0**

**1. Подготовка данных**

🗂️ **Основной файл** должен содержать:
• **Лист "мин запасы"** - основная логика
  - Номенклатура (названия товаров)
  - Активный/нет (YES/NO) 
  - Категории товаров
  - ADS по филиалам (казыбаева, барыс, астана, шымкент)
  - Минимальные запасы по филиалам
  - Фактические остатки по филиалам

🔤 **ABC файл** должен содержать:
• **Лист1** с данными:
  - Наименование товара
  - Категория
  - Годовые продажи (объем)

**2. Загрузка файлов** 📁
Отправьте файлы в чат или используйте кнопки:
• Сначала основной файл
• Затем ABC файл (опционально)

**3. ABC анализ** 🔤
• Автоматическая классификация A/B/C
• Парето-анализ 80/20
• Анализ по категориям
• Умное распределение полок

**4. Настройка параметров** ⚙️
• Коэффициент безопасности (1.0-2.0)
• Транзитное время (1-30 дней)
• Количество полок для распределения
• Дни запаса по категориям

**5. Формирование заказов** 📋
Система создает:
• Заказы по филиалам с ABC классами
• Учет активности ассортимента
• Расчет чистой потребности
• Применение коэффициента безопасности

**6. Получение результатов** 📤
• Расширенный Excel с множественными листами
• ABC анализ по категориям
• Умное распределение торгового пространства
• Детальная аналитика по филиалам

**Команды:**
/start - Начать работу
/help - Эта инструкция
/settings - Настройки параметров
/status - Статус обработки данных
/abc - Быстрый ABC анализ
/quality - Проверка качества данных
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /settings"""
        user_id = update.effective_user.id
        
        # Получаем текущие настройки пользователя
        settings = context.user_data.get('settings', {
            'safety_factor': 1.2,
            'transit_time': 7,
            'total_shelves': 786,
            'days_supply': 10,
            'use_abc_weighting': True
        })
        
        settings_text = f"""
⚙️ **Настройки системы v2.0**

🛡️ Коэффициент безопасности: {settings['safety_factor']}
🚛 Транзитное время: {settings['transit_time']} дней
🏪 Общее количество полок: {settings['total_shelves']}
📅 Дни запаса: {settings['days_supply']}
🔤 ABC взвешивание полок: {'Включено' if settings['use_abc_weighting'] else 'Отключено'}

**Объяснение параметров:**

🛡️ **Коэффициент безопасности** - увеличивает заказ сверх минимальной потребности
🚛 **Транзитное время** - дни доставки (учитывается в расчете чистой потребности)  
🏪 **Количество полок** - для расчета распределения торгового пространства
📅 **Дни запаса** - на сколько дней должен хватать товар
🔤 **ABC взвешивание** - A товары получают больше места на полках

Используйте кнопки для изменения:
        """
        
        keyboard = [
            [InlineKeyboardButton("🛡️ Коэфф. безопасности", callback_data='set_safety')],
            [InlineKeyboardButton("🚛 Транзитное время", callback_data='set_transit')],
            [InlineKeyboardButton("🏪 Количество полок", callback_data='set_shelves')],
            [InlineKeyboardButton("📅 Дни запаса", callback_data='set_days')],
            [InlineKeyboardButton("🔤 ABC взвешивание", callback_data='toggle_abc')],
            [InlineKeyboardButton("🔄 Сбросить настройки", callback_data='reset_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_systems:
            await update.message.reply_text("❌ Система не инициализирована. Используйте /start")
            return
        
        system = self.user_systems[user_id]
        
        status_text = "📊 **Статус системы v2.0**\n\n"
        
        # Проверяем загруженные данные
        if hasattr(system.processor, 'processed_data') and 'main' in system.processor.processed_data:
            main_df = system.processor.processed_data['main']
            status_text += "✅ **Основные данные загружены:**\n"
            status_text += f"• Товаров: {len(main_df)}\n"
            status_text += f"• Активных: {len(main_df[main_df['active_assortment'].str.upper() == 'YES'])}\n"
            status_text += f"• Категорий: {main_df['category'].nunique()}\n"
        else:
            status_text += "❌ Основные данные не загружены\n"
        
        # ABC данные
        if system.processor.abc_data is not None:
            abc_df = system.processor.abc_data
            status_text += f"\n✅ **ABC данные загружены:**\n"
            status_text += f"• Товаров: {len(abc_df)}\n"
            status_text += f"• Категорий: {abc_df['category'].nunique()}\n"
        else:
            status_text += "\n❌ ABC данные не загружены\n"
        
        # ABC анализ
        if system.abc_results:
            status_text += f"\n✅ ABC анализ выполнен: {len(system.abc_results)} категорий\n"
        else:
            status_text += "\n❌ ABC анализ не выполнен\n"
        
        # Анализ категорий
        if system.category_analysis:
            status_text += f"✅ Анализ категорий: {len(system.category_analysis)} категорий\n"
        else:
            status_text += "❌ Анализ категорий не проведен\n"
        
        # Заказы
        if system.orders_data is not None and not system.orders_data.empty:
            status_text += f"✅ Заказы сформированы: {len(system.orders_data)} позиций\n"
            
            # ABC статистика в заказах
            if 'abc_class' in system.orders_data.columns:
                abc_counts = system.orders_data['abc_class'].value_counts()
                status_text += f"  - A товары: {abc_counts.get('A', 0)}\n"
                status_text += f"  - B товары: {abc_counts.get('B', 0)}\n"
                status_text += f"  - C товары: {abc_counts.get('C', 0)}\n"
        else:
            status_text += "❌ Заказы не сформированы\n"
        
        # Кнопки для действий
        keyboard = []
        
        if hasattr(system.processor, 'processed_data') and 'main' in system.processor.processed_data:
            if system.processor.abc_data is not None:
                keyboard.append([InlineKeyboardButton("🔤 ABC анализ", callback_data='perform_abc')])
            keyboard.append([InlineKeyboardButton("📊 Анализ категорий", callback_data='analyze_categories')])
            keyboard.append([InlineKeyboardButton("📋 Сформировать заказы", callback_data='generate_orders')])
        
        if system.orders_data is not None and not system.orders_data.empty:
            keyboard.append([InlineKeyboardButton("📤 Скачать результаты", callback_data='export')])
        
        keyboard.append([InlineKeyboardButton("🔍 Качество данных", callback_data='check_quality')])
        keyboard.append([InlineKeyboardButton("🔄 Обновить статус", callback_data='status')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def abc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /abc - быстрый ABC анализ"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_systems:
            await update.message.reply_text("❌ Система не инициализирована. Используйте /start")
            return
        
        system = self.user_systems[user_id]
        
        if system.processor.abc_data is None:
            await update.message.reply_text("❌ ABC данные не загружены. Сначала отправьте файл ABC анализа.")
            return
        
        try:
            abc_results = system.perform_abc_analysis()
            
            if abc_results:
                abc_text = "🔤 **Быстрый ABC анализ**\n\n"
                
                # Общая статистика
                if 'abc_analysis' in system.processor.processed_data:
                    abc_data = system.processor.processed_data['abc_analysis']
                    abc_counts = abc_data['abc_class'].value_counts()
                    total = len(abc_data)
                    
                    abc_text += f"📊 **Общее распределение:**\n"
                    abc_text += f"🔴 A товары: {abc_counts.get('A', 0)} ({abc_counts.get('A', 0)/total*100:.1f}%)\n"
                    abc_text += f"🟡 B товары: {abc_counts.get('B', 0)} ({abc_counts.get('B', 0)/total*100:.1f}%)\n" 
                    abc_text += f"🟢 C товары: {abc_counts.get('C', 0)} ({abc_counts.get('C', 0)/total*100:.1f}%)\n\n"
                
                # Топ категории
                abc_text += "🏆 **Топ-5 категорий по продажам:**\n"
                sorted_categories = sorted(abc_results.items(), 
                                         key=lambda x: x[1]['sales_percentage'], reverse=True)
                
                for i, (category, data) in enumerate(sorted_categories[:5], 1):
                    abc_text += f"{i}. {category}: {data['sales_percentage']:.1f}%\n"
                    abc_text += f"   A/B/C: {data['abc_distribution']['A']}/{data['abc_distribution']['B']}/{data['abc_distribution']['C']}\n"
                
                keyboard = [
                    [InlineKeyboardButton("📊 Подробный анализ", callback_data='detailed_abc')],
                    [InlineKeyboardButton("📋 Сформировать заказы", callback_data='generate_orders')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(abc_text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Ошибка выполнения ABC анализа")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка ABC анализа: {str(e)}")
    
    async def quality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /quality - проверка качества данных"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_systems:
            await update.message.reply_text("❌ Система не инициализирована. Используйте /start")
            return
        
        system = self.user_systems[user_id]
        
        try:
            quality_report = system.get_data_quality_report()
            
            if quality_report:
                quality_text = "🔍 **Отчет о качестве данных**\n\n"
                
                # Основная статистика
                if 'main_data' in quality_report:
                    main_data = quality_report['main_data']
                    quality_text += "📊 **Основные данные:**\n"
                    quality_text += f"• Всего товаров: {main_data.get('total_items', 0)}\n"
                    quality_text += f"• С продажами: {main_data.get('items_with_ads', 0)}\n"
                    quality_text += f"• Активных: {main_data.get('active_items', 0)}\n"
                    quality_text += f"• Категорий: {main_data.get('categories_count', 0)}\n\n"
                
                # ABC покрытие
                if 'abc_coverage' in quality_report:
                    coverage = quality_report['abc_coverage']
                    if coverage >= 70:
                        quality_text += f"✅ ABC покрытие: {coverage}% (отлично)\n"
                    elif coverage >= 50:
                        quality_text += f"⚠️ ABC покрытие: {coverage}% (удовлетворительно)\n"
                    else:
                        quality_text += f"❌ ABC покрытие: {coverage}% (требует внимания)\n"
                
                # Проблемы
                if quality_report.get('issues'):
                    quality_text += "\n⚠️ **Обнаруженные проблемы:**\n"
                    for issue in quality_report['issues'][:3]:  # Показываем первые 3
                        quality_text += f"• {issue}\n"
                
                # Рекомендации
                if quality_report.get('recommendations'):
                    quality_text += "\n💡 **Рекомендации:**\n"
                    for rec in quality_report['recommendations'][:3]:
                        quality_text += f"• {rec}\n"
                
                await update.message.reply_text(quality_text, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Не удалось получить отчет о качестве данных")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка анализа качества: {str(e)}")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженных файлов"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_systems:
            self.user_systems[user_id] = InventoryAutomationSystemV2()
        
        document = update.message.document
        
        # Проверяем тип файла
        if not document.file_name.endswith(('.xlsx', '.xls')):
            await update.message.reply_text("❌ Пожалуйста, отправьте Excel файл (.xlsx или .xls)")
            return
        
        try:
            await update.message.reply_text("📥 Загружаю файл...")
            
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # Определяем тип файла по содержимому
            file_type = await self._detect_file_type(file_bytes, document.file_name)
            
            if file_type == 'main':
                success = await self._process_main_file(update, context, file_bytes, document.file_name)
            elif file_type == 'abc':
                success = await self._process_abc_file(update, context, file_bytes, document.file_name)
            else:
                # Спрашиваем у пользователя
                await self._ask_file_type(update, context, file_bytes, document.file_name)
                return
            
        except Exception as e:
            logger.error(f"Ошибка обработки файла: {str(e)}")
            await update.message.reply_text(f"❌ Ошибка обработки файла: {str(e)}")
    
    async def _detect_file_type(self, file_bytes, filename):
        """Автоматическое определение типа файла"""
        try:
            # Простое определение по названию
            filename_lower = filename.lower()
            
            if 'abc' in filename_lower or 'исходник' in filename_lower:
                return 'abc'
            elif 'мин' in filename_lower or 'запас' in filename_lower or 'ворк' in filename_lower:
                return 'main'
            else:
                return 'unknown'
                
        except:
            return 'unknown'
    
    async def _process_main_file(self, update, context, file_bytes, filename):
        """Обработка основного файла"""
        try:
            user_id = update.effective_user.id
            system = self.user_systems[user_id]
            
            # Сохраняем временно
            temp_filename = f"temp_main_{user_id}_{filename}"
            with open(temp_filename, 'wb') as f:
                f.write(file_bytes)
            
            await update.message.reply_text("🔄 Обрабатываю основные данные...")
            
            # Загружаем и обрабатываем
            structure_info = system.processor.load_excel_file(temp_filename)
            main_df = system.processor.process_main_data()
            
            # Формируем отчет
            report = "✅ **Основной файл успешно загружен!**\n\n"
            report += f"📊 **Обработано товаров:** {len(main_df)}\n"
            report += f"✅ **Активных товаров:** {len(main_df[main_df['active_assortment'].str.upper() == 'YES'])}\n"
            report += f"📈 **С продажами:** {len(main_df[main_df['total_ads'] > 0])}\n"
            report += f"🏷️ **Категорий:** {main_df['category'].nunique()}\n\n"
            
            # Распределение по филиалам
            report += "🏪 **ADS по филиалам:**\n"
            report += f"• Казыбаева: {main_df['ads_kaz'].sum():.1f}\n"
            report += f"• Барыс: {main_df['ads_bar'].sum():.1f}\n"
            report += f"• Астана: {main_df['ads_ast'].sum():.1f}\n"
            report += f"• Шымкент: {main_df['ads_shy'].sum():.1f}\n"
            
            keyboard = [
                [InlineKeyboardButton("📊 Анализ категорий", callback_data='analyze_categories')],
                [InlineKeyboardButton("🔤 Загрузить ABC", callback_data='upload_abc')],
                [InlineKeyboardButton("📋 Статус", callback_data='status')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(report, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Удаляем временный файл
            os.remove(temp_filename)
            return True
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки основного файла: {str(e)}")
            return False
    
    async def _process_abc_file(self, update, context, file_bytes, filename):
        """Обработка ABC файла"""
        try:
            user_id = update.effective_user.id
            system = self.user_systems[user_id]
            
            # Сохраняем временно
            temp_filename = f"temp_abc_{user_id}_{filename}"
            with open(temp_filename, 'wb') as f:
                f.write(file_bytes)
            
            await update.message.reply_text("🔄 Обрабатываю ABC данные...")
            
            # Загружаем ABC данные
            abc_df = system.processor.load_abc_analysis_data(temp_filename)
            
            # Формируем отчет
            report = "✅ **ABC файл успешно загружен!**\n\n"
            report += f"🔤 **Товаров для ABC:** {len(abc_df)}\n"
            report += f"💰 **Общие продажи:** {abc_df['annual_sales'].sum():,.0f}\n"
            report += f"🏷️ **Категорий:** {abc_df['category'].nunique()}\n\n"
            
            # Топ товары
            top_items = abc_df.nlargest(5, 'annual_sales')
            report += "🏆 **Топ-5 товаров:**\n"
            for _, item in top_items.iterrows():
                report += f"• {item['nomenclature']}: {item['annual_sales']:,.0f}\n"
            
            keyboard = [
                [InlineKeyboardButton("🔤 Выполнить ABC анализ", callback_data='perform_abc')],
                [InlineKeyboardButton("📊 Анализ категорий", callback_data='analyze_categories')],
                [InlineKeyboardButton("📋 Статус", callback_data='status')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(report, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Удаляем временный файл
            os.remove(temp_filename)
            return True
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки ABC файла: {str(e)}")
            return False
    
    async def _ask_file_type(self, update, context, file_bytes, filename):
        """Запрос типа файла у пользователя"""
        # Сохраняем файл в контексте пользователя
        context.user_data['pending_file'] = {
            'bytes': file_bytes,
            'filename': filename
        }
        
        keyboard = [
            [InlineKeyboardButton("📊 Основной файл (мин запасы)", callback_data='file_type_main')],
            [InlineKeyboardButton("🔤 ABC файл (исходники)", callback_data='file_type_abc')],
            [InlineKeyboardButton("❌ Отмена", callback_data='file_type_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤔 **Не удалось определить тип файла автоматически.**\n\n"
            "Пожалуйста, укажите тип файла:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок"""
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        
        if user_id not in self.user_systems:
            self.user_systems[user_id] = InventoryAutomationSystemV2()
        
        system = self.user_systems[user_id]
        
        # Основные команды
        if query.data == 'help':
            await self.help_command(update, context)
        
        elif query.data == 'settings':
            await self.settings_command(update, context)
        
        elif query.data == 'status':
            await self.status_command(update, context)
        
        # Загрузка файлов
        elif query.data == 'upload_main':
            await query.edit_message_text(
                "📁 **Загрузка основного файла**\n\n"
                "Отправьте Excel файл с основными данными.\n"
                "Файл должен содержать лист 'мин запасы' с полной структурой данных.",
                parse_mode='Markdown'
            )
        
        elif query.data == 'upload_abc':
            await query.edit_message_text(
                "🔤 **Загрузка ABC файла**\n\n"
                "Отправьте Excel файл с данными для ABC анализа.\n"
                "Файл должен содержать товары и их годовые продажи.",
                parse_mode='Markdown'
            )
        
        # Определение типа файла
        elif query.data.startswith('file_type_'):
            await self._handle_file_type_selection(update, context, query.data)
        
        # ABC анализ
        elif query.data == 'perform_abc':
            await self._perform_abc_analysis(update, context, system)
        
        elif query.data == 'detailed_abc':
            await self._show_detailed_abc(update, context, system)
        
        # Анализ категорий
        elif query.data == 'analyze_categories':
            await self._analyze_categories(update, context, system)
        
        # Генерация заказов
        elif query.data == 'generate_orders':
            await self._generate_orders(update, context, system)
        
        # Экспорт
        elif query.data == 'export':
            await self._export_results(update, context, system)
        
        # Качество данных
        elif query.data == 'check_quality':
            await self.quality_command(update, context)
        
        # Настройки
        elif query.data.startswith('set_') or query.data == 'toggle_abc' or query.data == 'reset_settings':
            await self._handle_settings_change(update, context, query.data)
    
    async def _handle_file_type_selection(self, update, context, data_type):
        """Обработка выбора типа файла"""
        if 'pending_file' not in context.user_data:
            await update.callback_query.edit_message_text("❌ Файл не найден. Загрузите файл заново.")
            return
        
        file_info = context.user_data['pending_file']
        file_bytes = file_info['bytes']
        filename = file_info['filename']
        
        if data_type == 'file_type_main':
            await update.callback_query.edit_message_text("🔄 Обрабатываю как основной файл...")
            success = await self._process_main_file(update, context, file_bytes, filename)
        
        elif data_type == 'file_type_abc':
            await update.callback_query.edit_message_text("🔄 Обрабатываю как ABC файл...")
            success = await self._process_abc_file(update, context, file_bytes, filename)
        
        elif data_type == 'file_type_cancel':
            await update.callback_query.edit_message_text("❌ Загрузка файла отменена.")
            success = False
        
        # Очищаем временные данные
        del context.user_data['pending_file']
    
    async def _perform_abc_analysis(self, update, context, system):
        """Выполнение ABC анализа"""
        try:
            await update.callback_query.edit_message_text("🔄 Выполняю ABC анализ...")
            
            if system.processor.abc_data is None:
                await update.callback_query.edit_message_text("❌ ABC данные не загружены")
                return
            
            abc_results = system.perform_abc_analysis()
            
            if abc_results:
                abc_text = "✅ **ABC анализ завершен!**\n\n"
                
                # Общая статистика
                if 'abc_analysis' in system.processor.processed_data:
                    abc_data = system.processor.processed_data['abc_analysis']
                    abc_counts = abc_data['abc_class'].value_counts()
                    total = len(abc_data)
                    
                    abc_text += f"📊 **Общая статистика:**\n"
                    abc_text += f"🔴 A товары: {abc_counts.get('A', 0)} ({abc_counts.get('A', 0)/total*100:.1f}%)\n"
                    abc_text += f"🟡 B товары: {abc_counts.get('B', 0)} ({abc_counts.get('B', 0)/total*100:.1f}%)\n"
                    abc_text += f"🟢 C товары: {abc_counts.get('C', 0)} ({abc_counts.get('C', 0)/total*100:.1f}%)\n\n"
                
                abc_text += f"🏷️ **Категорий проанализировано:** {len(abc_results)}\n\n"
                
                # Топ категории
                sorted_categories = sorted(abc_results.items(), 
                                         key=lambda x: x[1]['sales_percentage'], reverse=True)
                
                abc_text += "🏆 **Топ-5 категорий по продажам:**\n"
                for i, (category, data) in enumerate(sorted_categories[:5], 1):
                    abc_text += f"{i}. {category[:30]}{'...' if len(category) > 30 else ''}\n"
                    abc_text += f"   💰 {data['sales_percentage']:.1f}% | A:{data['abc_distribution']['A']} B:{data['abc_distribution']['B']} C:{data['abc_distribution']['C']}\n"
                
                keyboard = [
                    [InlineKeyboardButton("📊 Анализ категорий", callback_data='analyze_categories')],
                    [InlineKeyboardButton("📋 Сформировать заказы", callback_data='generate_orders')],
                    [InlineKeyboardButton("📤 Подробный отчет", callback_data='detailed_abc')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    abc_text, reply_markup=reply_markup, parse_mode='Markdown'
                )
            else:
                await update.callback_query.edit_message_text("❌ Не удалось выполнить ABC анализ")
                
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка ABC анализа: {str(e)}")
    
    async def _show_detailed_abc(self, update, context, system):
        """Показ детального ABC анализа"""
        try:
            if not system.abc_results:
                await update.callback_query.edit_message_text("❌ ABC анализ не выполнен")
                return
            
            # Создаем детальный отчет
            detailed_text = "📊 **Детальный ABC анализ по категориям**\n\n"
            
            sorted_categories = sorted(system.abc_results.items(), 
                                     key=lambda x: x[1]['sales_percentage'], reverse=True)
            
            for i, (category, data) in enumerate(sorted_categories[:10], 1):  # Топ-10
                detailed_text += f"**{i}. {category[:25]}{'...' if len(category) > 25 else ''}**\n"
                detailed_text += f"💰 Продажи: {data['sales_percentage']:.2f}% ({data['total_sales']:,.0f})\n"
                detailed_text += f"📦 Товаров: {data['total_items']}\n"
                detailed_text += f"🔴A: {data['abc_distribution']['A']} "
                detailed_text += f"🟡B: {data['abc_distribution']['B']} "
                detailed_text += f"🟢C: {data['abc_distribution']['C']}\n\n"
                
                if len(detailed_text) > 3000:  # Ограничение Telegram
                    detailed_text += f"... и еще {len(sorted_categories) - i} категорий"
                    break
            
            keyboard = [
                [InlineKeyboardButton("📋 Сформировать заказы", callback_data='generate_orders')],
                [InlineKeyboardButton("🔙 Назад к статусу", callback_data='status')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                detailed_text, reply_markup=reply_markup, parse_mode='Markdown'
            )
            
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка показа ABC: {str(e)}")
    
    async def _analyze_categories(self, update, context, system):
        """Анализ категорий с ABC"""
        try:
            await update.callback_query.edit_message_text("🔄 Анализирую категории с ABC...")
            
            if 'main' not in system.processor.processed_data:
                await update.callback_query.edit_message_text("❌ Основные данные не загружены")
                return
            
            # Выполняем анализ
            category_analysis = system.analyze_categories_with_abc()
            
            if category_analysis:
                # Получаем настройки для расчета полок
                settings = context.user_data.get('settings', {'total_shelves': 786})
                space_dist = system.calculate_space_distribution_with_abc(settings['total_shelves'])
                
                analysis_text = "📊 **Анализ категорий завершен!**\n\n"
                analysis_text += f"🏷️ **Категорий проанализировано:** {len(category_analysis)}\n"
                analysis_text += f"🏪 **Полок распределено:** {settings['total_shelves']}\n\n"
                
                # Топ категории по ADS
                sorted_cats = sorted(category_analysis.items(), 
                                   key=lambda x: x[1]['ads_percentage'], reverse=True)
                
                analysis_text += "🏆 **Топ-5 категорий по ADS:**\n"
                for i, (cat, data) in enumerate(sorted_cats[:5], 1):
                    analysis_text += f"{i}. {cat[:25]}{'...' if len(cat) > 25 else ''}\n"
                    analysis_text += f"   📈 ADS: {data['ads_percentage']:.1f}%"
                    
                    if space_dist and cat in space_dist:
                        analysis_text += f" | 🏪 Полок: {space_dist[cat]['adjusted_shelves']}"
                    
                    analysis_text += f"\n   🔤 A:{data['abc_distribution']['A']} B:{data['abc_distribution']['B']} C:{data['abc_distribution']['C']}\n"
                
                keyboard = [
                    [InlineKeyboardButton("📋 Сформировать заказы", callback_data='generate_orders')],
                    [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
                    [InlineKeyboardButton("📊 Статус", callback_data='status')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    analysis_text, reply_markup=reply_markup, parse_mode='Markdown'
                )
            else:
                await update.callback_query.edit_message_text("❌ Не удалось выполнить анализ категорий")
                
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка анализа категорий: {str(e)}")
    
    async def _generate_orders(self, update, context, system):
        """Генерация заказов"""
        try:
            await update.callback_query.edit_message_text("🔄 Формирую заказы по логике Саната...")
            
            if 'main' not in system.processor.processed_data:
                await update.callback_query.edit_message_text("❌ Основные данные не загружены")
                return
            
            # Получаем настройки
            settings = context.user_data.get('settings', {
                'safety_factor': 1.2,
                'transit_time': 7
            })
            
            # Генерируем заказы
            orders_df = system.generate_orders_with_full_logic(
                settings['safety_factor'], 
                settings['transit_time']
            )
            
            if not orders_df.empty:
                # Получаем расширенную сводку
                branch_summary = system.get_enhanced_branch_summary()
                
                orders_text = "✅ **Заказы сформированы успешно!**\n\n"
                orders_text += f"📋 **Общая статистика:**\n"
                orders_text += f"• Позиций: {len(orders_df)}\n"
                orders_text += f"• Количество: {orders_df['pre_order'].sum():,.0f}\n"
                orders_text += f"• Филиалов: {orders_df['branch'].nunique()}\n"
                orders_text += f"• Категорий: {orders_df['category'].nunique()}\n\n"
                
                # ABC распределение в заказах
                if 'abc_class' in orders_df.columns:
                    abc_counts = orders_df['abc_class'].value_counts()
                    orders_text += f"🔤 **ABC в заказах:**\n"
                    orders_text += f"🔴 A: {abc_counts.get('A', 0)} ({abc_counts.get('A', 0)/len(orders_df)*100:.1f}%)\n"
                    orders_text += f"🟡 B: {abc_counts.get('B', 0)} ({abc_counts.get('B', 0)/len(orders_df)*100:.1f}%)\n"
                    orders_text += f"🟢 C: {abc_counts.get('C', 0)} ({abc_counts.get('C', 0)/len(orders_df)*100:.1f}%)\n\n"
                
                # Статистика по филиалам
                if branch_summary:
                    orders_text += "🏪 **По филиалам:**\n"
                    for branch, data in branch_summary.items():
                        orders_text += f"• {branch}: {data['total_positions']} поз. ({data['total_quantity']:,.0f})\n"
                
                keyboard = [
                    [InlineKeyboardButton("📤 Скачать Excel", callback_data='export')],
                    [InlineKeyboardButton("📊 Детали по филиалам", callback_data='branch_details')],
                    [InlineKeyboardButton("⚙️ Изменить параметры", callback_data='settings')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    orders_text, reply_markup=reply_markup, parse_mode='Markdown'
                )
            else:
                await update.callback_query.edit_message_text(
                    "⚠️ **Не найдено позиций для заказа**\n\n"
                    "Возможные причины:\n"
                    "• Все товары имеют достаточные остатки\n"
                    "• Товары неактивны (active_assortment = NO)\n"
                    "• Отсутствуют продажи (ADS = 0)\n\n"
                    "Проверьте настройки или данные."
                )
                
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка генерации заказов: {str(e)}")
    
    async def _export_results(self, update, context, system):
        """Экспорт результатов"""
        try:
            await update.callback_query.edit_message_text("📤 Подготавливаю расширенный Excel файл...")
            
            if system.orders_data is None or system.orders_data.empty:
                await update.callback_query.edit_message_text("❌ Нет данных для экспорта")
                return
            
            # Генерируем Excel файл
            excel_buffer = system.export_enhanced_results()
            
            if not excel_buffer:
                await update.callback_query.edit_message_text("❌ Ошибка создания Excel файла")
                return
            
            # Отправляем файл
            excel_buffer.seek(0)
            filename = f"inventory_orders_enhanced_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx"
            
            # Создаем описание содержимого
            caption = "📊 **Расширенный отчет по товарным запасам v2.0**\n\n"
            caption += "**📁 Содержимое файла:**\n"
            caption += "• Все_заказы - Полный список с ABC\n"
            caption += "• Заказы_[филиал] - По каждому филиалу\n"
            caption += "• Сводка_филиалов - Статистика с ABC\n"
            caption += "• Анализ_категорий_ABC - Категории с ABC\n"
            caption += "• Распределение_полок_ABC - Умное распределение\n"
            caption += "• ABC_анализ_категорий - Результаты ABC\n"
            caption += "• ABC_детали - Все товары с классами\n"
            caption += "• Общая_сводка - Итоговая информация\n\n"
            
            # Статистика файла
            if system.orders_data is not None:
                orders_df = system.orders_data
                caption += f"📈 **Статистика:**\n"
                caption += f"• Позиций: {len(orders_df)}\n"
                caption += f"• Общее количество: {orders_df['pre_order'].sum():,.0f}\n"
                
                if 'abc_class' in orders_df.columns:
                    abc_counts = orders_df['abc_class'].value_counts()
                    caption += f"• A товары: {abc_counts.get('A', 0)}\n"
                    caption += f"• B товары: {abc_counts.get('B', 0)}\n"
                    caption += f"• C товары: {abc_counts.get('C', 0)}\n"
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=InputFile(excel_buffer, filename=filename),
                caption=caption,
                parse_mode='Markdown'
            )
            
            await update.callback_query.edit_message_text("✅ Расширенный Excel файл отправлен!")
            
        except Exception as e:
            logger.error(f"Ошибка экспорта: {str(e)}")
            await update.callback_query.edit_message_text(f"❌ Ошибка экспорта: {str(e)}")
    
    async def _handle_settings_change(self, update, context, setting_type):
        """Обработка изменения настроек"""
        settings = context.user_data.get('settings', {
            'safety_factor': 1.2,
            'transit_time': 7,
            'total_shelves': 786,
            'days_supply': 10,
            'use_abc_weighting': True
        })
        
        if setting_type == 'reset_settings':
            context.user_data['settings'] = {
                'safety_factor': 1.2,
                'transit_time': 7,
                'total_shelves': 786,
                'days_supply': 10,
                'use_abc_weighting': True
            }
            await update.callback_query.edit_message_text("✅ Настройки сброшены к значениям по умолчанию")
        
        elif setting_type == 'toggle_abc':
            settings['use_abc_weighting'] = not settings.get('use_abc_weighting', True)
            context.user_data['settings'] = settings
            status = "включено" if settings['use_abc_weighting'] else "отключено"
            await update.callback_query.edit_message_text(f"✅ ABC взвешивание полок {status}")
        
        else:
            # Для остальных настроек показываем инструкцию
            instructions = {
                'set_safety': "🛡️ Для изменения коэффициента безопасности отправьте:\n`/set_safety 1.5`\n\n(Допустимые значения: 1.0-2.0)",
                'set_transit': "🚛 Для изменения транзитного времени отправьте:\n`/set_transit 10`\n\n(Допустимые значения: 1-30 дней)",
                'set_shelves': "🏪 Для изменения количества полок отправьте:\n`/set_shelves 1000`\n\n(Допустимые значения: 100-2000)",
                'set_days': "📅 Для изменения дней запаса отправьте:\n`/set_days 15`\n\n(Допустимые значения: 5-30 дней)"
            }
            
            instruction = instructions.get(setting_type, "❌ Неизвестная настройка")
            await update.callback_query.edit_message_text(instruction, parse_mode='Markdown')

def main():
    """Запуск обновленного бота"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Установите токен бота в переменную окружения TELEGRAM_BOT_TOKEN")
        return
    
    # Создаем экземпляр обновленного бота
    bot = InventoryBotV2()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("settings", bot.settings_command))
    application.add_handler(CommandHandler("status", bot.status_command))
    application.add_handler(CommandHandler("abc", bot.abc_command))
    application.add_handler(CommandHandler("quality", bot.quality_command))
    
    # Обработчик документов
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
    
    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # Запускаем бота
    print("🤖 Обновленный бот v2.0 запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == '__main__':
    main()