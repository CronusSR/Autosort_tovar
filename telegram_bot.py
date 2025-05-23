#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram бот для системы автоматизации товарных запасов
Интерфейс для работы с системой Саната через Telegram
"""

import logging
import os
import io
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from excel_processor import ExcelDataProcessor
from inventory_automation import InventoryAutomationSystem

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (получить от @BotFather)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

class InventoryBot:
    """Класс Telegram бота для системы управления запасами"""
    
    def __init__(self):
        self.user_systems = {}  # Хранилище систем для каждого пользователя
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_id = update.effective_user.id
        
        # Инициализируем систему для пользователя
        self.user_systems[user_id] = InventoryAutomationSystem()
        
        welcome_text = """
🤖 **Система автоматизации товарных запасов**

Привет! Я помогу вам автоматизировать управление товарными запасами по логике Саната.

**Что я умею:**
📊 Анализировать категории товаров
📋 Формировать заказы автоматически  
📤 Экспортировать результаты в Excel
⚙️ Учитывать кратность упаковки

**Как начать:**
1. Отправьте мне Excel файл с данными
2. Настройте параметры расчета
3. Получите готовые заказы

Отправьте /help для подробной инструкции.
        """
        
        keyboard = [
            [InlineKeyboardButton("📁 Загрузить данные", callback_data='upload')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
📖 **Подробная инструкция**

**1. Подготовка данных**
Ваш Excel файл должен содержать листы:
• **ADS** - среднедневные продажи
• **Stock Balance** - текущие остатки
• **Min-Target** - минимальные запасы по филиалам

**2. Загрузка файла**
Просто отправьте Excel файл в чат

**3. Настройка параметров** ⚙️
• Количество дней запаса (5-30)
• Общее количество полок
• Коэффициент безопасности
• Кратность упаковки

**4. Получение результатов**
Система сформирует:
• Анализ категорий товаров
• Распределение торгового пространства  
• Список заказов с количествами
• Excel файл для скачивания

**Команды:**
/start - Начать работу
/help - Эта инструкция
/settings - Настройки параметров
/status - Статус обработки данных
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /settings"""
        user_id = update.effective_user.id
        
        # Получаем текущие настройки пользователя
        settings = context.user_data.get('settings', {
            'days_supply': 10,
            'total_shelves': 786,
            'safety_factor': 1.2,
            'package_multiple': 4,
            'use_package_multiples': False
        })
        
        settings_text = f"""
⚙️ **Текущие настройки**

📅 Дней запаса: {settings['days_supply']}
🏪 Общее количество полок: {settings['total_shelves']}
🛡️ Коэффициент безопасности: {settings['safety_factor']}
📦 Кратность упаковки: {settings['package_multiple']}
✅ Учитывать кратность: {'Да' if settings['use_package_multiples'] else 'Нет'}

Используйте кнопки ниже для изменения настроек:
        """
        
        keyboard = [
            [InlineKeyboardButton("📅 Дни запаса", callback_data='set_days')],
            [InlineKeyboardButton("🏪 Количество полок", callback_data='set_shelves')],
            [InlineKeyboardButton("🛡️ Коэффициент безопасности", callback_data='set_safety')],
            [InlineKeyboardButton("📦 Кратность упаковки", callback_data='set_package')],
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
        
        # Проверяем состояние системы
        status_text = "📊 **Статус системы**\n\n"
        
        # Проверяем загруженные данные
        if hasattr(system.processor, 'processed_data') and system.processor.processed_data:
            status_text += "✅ **Данные загружены:**\n"
            for data_type in system.processor.processed_data.keys():
                df = system.processor.processed_data[data_type]
                status_text += f"• {data_type.upper()}: {len(df)} записей\n"
        else:
            status_text += "❌ Данные не загружены\n"
        
        # Проверяем проведенные анализы
        if system.category_analysis:
            status_text += f"\n✅ Анализ категорий: {len(system.category_analysis)} категорий\n"
        else:
            status_text += "\n❌ Анализ категорий не проведен\n"
        
        if system.orders_data is not None and not system.orders_data.empty:
            status_text += f"✅ Заказы сформированы: {len(system.orders_data)} позиций\n"
        else:
            status_text += "❌ Заказы не сформированы\n"
        
        # Кнопки для действий
        keyboard = []
        if hasattr(system.processor, 'processed_data') and system.processor.processed_data:
            keyboard.append([InlineKeyboardButton("📊 Анализ категорий", callback_data='analyze')])
            keyboard.append([InlineKeyboardButton("📋 Сформировать заказы", callback_data='generate_orders')])
        
        if system.orders_data is not None and not system.orders_data.empty:
            keyboard.append([InlineKeyboardButton("📤 Скачать результаты", callback_data='export')])
        
        keyboard.append([InlineKeyboardButton("🔄 Обновить статус", callback_data='status')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженных файлов"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_systems:
            self.user_systems[user_id] = InventoryAutomationSystem()
        
        document = update.message.document
        
        # Проверяем тип файла
        if not document.file_name.endswith(('.xlsx', '.xls')):
            await update.message.reply_text("❌ Пожалуйста, отправьте Excel файл (.xlsx или .xls)")
            return
        
        try:
            # Загружаем файл
            await update.message.reply_text("📥 Загружаю файл...")
            
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # Сохраняем временно
            temp_filename = f"temp_{user_id}_{document.file_name}"
            with open(temp_filename, 'wb') as f:
                f.write(file_bytes)
            
            # Обрабатываем файл
            await update.message.reply_text("🔄 Обрабатываю данные...")
            
            system = self.user_systems[user_id]
            structure_info = system.processor.load_excel_file(temp_filename)
            
            # Формируем отчет о загруженных данных
            report = "✅ **Файл успешно загружен!**\n\n"
            report += f"📊 **Найдено листов:** {len(structure_info)}\n\n"
            
            for sheet_name, info in structure_info.items():
                report += f"**{sheet_name}:**\n"
                report += f"• Строк: {info['rows']}\n"
                report += f"• Колонок: {info['columns']}\n\n"
            
            # Пытаемся обработать каждый тип данных
            processed_types = []
            
            try:
                ads_df = system.processor.process_ads_data()
                processed_types.append(f"✅ ADS: {len(ads_df)} записей")
            except Exception as e:
                processed_types.append(f"⚠️ ADS: {str(e)}")
            
            try:
                stock_df = system.processor.process_stock_data()
                processed_types.append(f"✅ Остатки: {len(stock_df)} записей")
            except Exception as e:
                processed_types.append(f"⚠️ Остатки: {str(e)}")
            
            try:
                target_df = system.processor.process_min_target_data()
                processed_types.append(f"✅ Min-Target: {len(target_df)} записей")
            except Exception as e:
                processed_types.append(f"⚠️ Min-Target: {str(e)}")
            
            report += "**Обработанные данные:**\n"
            report += "\n".join(processed_types)
            
            # Кнопки для дальнейших действий
            keyboard = [
                [InlineKeyboardButton("📊 Анализ категорий", callback_data='analyze')],
                [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
                [InlineKeyboardButton("📋 Статус", callback_data='status')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(report, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Удаляем временный файл
            os.remove(temp_filename)
            
        except Exception as e:
            logger.error(f"Ошибка обработки файла: {str(e)}")
            await update.message.reply_text(f"❌ Ошибка обработки файла: {str(e)}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок"""
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        
        if user_id not in self.user_systems:
            self.user_systems[user_id] = InventoryAutomationSystem()
        
        system = self.user_systems[user_id]
        
        if query.data == 'help':
            await self.help_command(update, context)
        
        elif query.data == 'settings':
            await self.settings_command(update, context)
        
        elif query.data == 'status':
            await self.status_command(update, context)
        
        elif query.data == 'analyze':
            await self.analyze_categories(update, context, system)
        
        elif query.data == 'generate_orders':
            await self.generate_orders(update, context, system)
        
        elif query.data == 'export':
            await self.export_results(update, context, system)
        
        elif query.data.startswith('set_'):
            await self.handle_settings_change(update, context, query.data)
        
        elif query.data == 'reset_settings':
            await self.reset_settings(update, context)
    
    async def analyze_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE, system):
        """Анализ категорий товаров"""
        try:
            await update.callback_query.edit_message_text("🔄 Выполняю анализ категорий...")
            
            # Получаем настройки
            settings = context.user_data.get('settings', {'total_shelves': 786})
            
            # Анализируем категории
            category_analysis = system.analyze_categories()
            
            if not category_analysis:
                await update.callback_query.edit_message_text("❌ Не удалось выполнить анализ категорий")
                return
            
            # Рассчитываем распределение пространства
            space_distribution = system.calculate_space_distribution(settings['total_shelves'])
            
            # Формируем отчет
            report = "📊 **Анализ категорий завершен!**\n\n"
            report += f"**Найдено категорий:** {len(category_analysis)}\n\n"
            
            # Топ-5 категорий по количеству товаров
            sorted_categories = sorted(category_analysis.items(), 
                                     key=lambda x: x[1]['item_count'], reverse=True)
            
            report += "**Топ-5 по количеству товаров:**\n"
            for i, (category, data) in enumerate(sorted_categories[:5], 1):
                report += f"{i}. {category}: {data['item_count']} товаров ({data['percentage']:.1f}%)\n"
            
            # Информация о распределении полок
            if space_distribution:
                report += f"\n**Распределение {settings['total_shelves']} полок:**\n"
                sorted_space = sorted(space_distribution.items(), 
                                    key=lambda x: x[1]['shelves'], reverse=True)
                
                for category, data in sorted_space[:5]:
                    report += f"• {category}: {data['shelves']} полок\n"
            
            keyboard = [
                [InlineKeyboardButton("📋 Сформировать заказы", callback_data='generate_orders')],
                [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
                [InlineKeyboardButton("📊 Подробный отчет", callback_data='detailed_report')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(report, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка анализа категорий: {str(e)}")
            await update.callback_query.edit_message_text(f"❌ Ошибка анализа: {str(e)}")
    
    async def generate_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE, system):
        """Генерация заказов"""
        try:
            await update.callback_query.edit_message_text("🔄 Формирую заказы...")
            
            # Получаем настройки
            settings = context.user_data.get('settings', {
                'days_supply': 10,
                'safety_factor': 1.2,
                'package_multiple': 4,
                'use_package_multiples': False
            })
            
            # Рассчитываем минимальные запасы
            min_stock_df = system.calculate_minimum_stock(settings['days_supply'])
            
            if min_stock_df.empty:
                await update.callback_query.edit_message_text("❌ Не удалось рассчитать минимальные запасы")
                return
            
            # Подготавливаем кратности упаковки
            package_multiples = None
            if settings['use_package_multiples']:
                package_multiples = {}
                if 'sku' in min_stock_df.columns:
                    for sku in min_stock_df['sku']:
                        package_multiples[sku] = settings['package_multiple']
            
            # Генерируем заказы
            orders_df = system.generate_orders(settings['safety_factor'], package_multiples)
            
            if orders_df.empty:
                await update.callback_query.edit_message_text("⚠️ Не найдено позиций для заказа")
                return
            
            # Формируем отчет
            report = "📋 **Заказы сформированы!**\n\n"
            report += f"**Позиций к заказу:** {len(orders_df)}\n"
            report += f"**Общее количество:** {orders_df['order_quantity'].sum():,.0f}\n"
            
            if 'order_value' in orders_df.columns:
                total_value = orders_df['order_value'].sum()
                report += f"**Общая стоимость:** {total_value:,.2f}\n"
            
            # Статистика по категориям
            if 'category' in orders_df.columns:
                category_stats = orders_df.groupby('category')['order_quantity'].sum().head(5)
                report += "\n**Топ-5 категорий по количеству:**\n"
                for category, qty in category_stats.items():
                    report += f"• {category}: {qty:,.0f}\n"
            
            keyboard = [
                [InlineKeyboardButton("📤 Скачать Excel", callback_data='export')],
                [InlineKeyboardButton("📊 Подробная статистика", callback_data='order_stats')],
                [InlineKeyboardButton("⚙️ Изменить настройки", callback_data='settings')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(report, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка генерации заказов: {str(e)}")
            await update.callback_query.edit_message_text(f"❌ Ошибка генерации заказов: {str(e)}")
    
    async def export_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, system):
        """Экспорт результатов в Excel"""
        try:
            await update.callback_query.edit_message_text("📤 Подготавливаю Excel файл...")
            
            if system.orders_data is None or system.orders_data.empty:
                await update.callback_query.edit_message_text("❌ Нет данных для экспорта")
                return
            
            # Генерируем Excel файл
            excel_buffer = system.export_results()
            
            if not excel_buffer:
                await update.callback_query.edit_message_text("❌ Ошибка создания Excel файла")
                return
            
            # Отправляем файл
            excel_buffer.seek(0)
            filename = f"inventory_orders_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx"
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=excel_buffer,
                filename=filename,
                caption="📊 **Результаты анализа товарных запасов**\n\n" +
                       "**Содержимое файла:**\n" +
                       "• Orders - Список заказов\n" +
                       "• Category_Analysis - Анализ категорий\n" +
                       "• Space_Distribution - Распределение пространства\n" +
                       "• Summary - Сводная информация",
                parse_mode='Markdown'
            )
            
            await update.callback_query.edit_message_text("✅ Excel файл отправлен!")
            
        except Exception as e:
            logger.error(f"Ошибка экспорта: {str(e)}")
            await update.callback_query.edit_message_text(f"❌ Ошибка экспорта: {str(e)}")
    
    async def handle_settings_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, setting_type):
        """Обработка изменения настроек"""
        # Здесь можно реализовать интерактивное изменение настроек
        # Для простоты пока просто отправляем инструкцию
        
        instructions = {
            'set_days': "📅 Чтобы изменить количество дней запаса, отправьте сообщение в формате:\n`/set_days 15`",
            'set_shelves': "🏪 Чтобы изменить количество полок, отправьте сообщение в формате:\n`/set_shelves 1000`",
            'set_safety': "🛡️ Чтобы изменить коэффициент безопасности, отправьте сообщение в формате:\n`/set_safety 1.5`",
            'set_package': "📦 Чтобы изменить кратность упаковки, отправьте сообщение в формате:\n`/set_package 6`"
        }
        
        instruction = instructions.get(setting_type, "❌ Неизвестная настройка")
        await update.callback_query.edit_message_text(instruction, parse_mode='Markdown')
    
    async def reset_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сброс настроек к значениям по умолчанию"""
        context.user_data['settings'] = {
            'days_supply': 10,
            'total_shelves': 786,
            'safety_factor': 1.2,
            'package_multiple': 4,
            'use_package_multiples': False
        }
        
        await update.callback_query.edit_message_text("✅ Настройки сброшены к значениям по умолчанию")

def main():
    """Запуск бота"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Установите токен бота в переменную окружения TELEGRAM_BOT_TOKEN")
        return
    
    # Создаем экземпляр бота
    bot = InventoryBot()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("settings", bot.settings_command))
    application.add_handler(CommandHandler("status", bot.status_command))
    
    # Обработчик документов
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
    
    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # Запускаем бота
    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == '__main__':
    main()