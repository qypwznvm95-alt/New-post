import asyncio
import logging
from datetime import datetime
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

import openai

from config import BOT_TOKEN, OPENAI_API_KEY, ADMIN_IDS, DB_PATH, EXPORT_DIR
from database import DatabaseManager
from analytics import AnalyticsExporter
from pdf_generator import PDFGenerator

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CarSalesBot:
    def __init__(self):
        self.db = DatabaseManager(DB_PATH)
        self.exporter = AnalyticsExporter(DB_PATH, EXPORT_DIR)
        self.pdf_gen = PDFGenerator()
        openai.api_key = OPENAI_API_KEY
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        
        # Сохраняем пользователя в базу
        self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name or ""
        )
        
        # Логируем команду
        self.db.log_message(user.id, "/start", "command")
        
        # Создаем меню
        keyboard = [
            [InlineKeyboardButton("🚗 Интересуюсь автомобилями", callback_data="interest_cars")],
            [InlineKeyboardButton("📊 Анализ региона", callback_data="analyze_region")],
            [InlineKeyboardButton("📄 Получить КП", callback_data="get_offer")],
        ]
        
        if user.id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("📊 Выгрузка данных", callback_data="admin_export")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Добро пожаловать, {user.first_name}!\n\n"
            "Я помогу вам с покупкой автомобиля и предоставлю аналитику по вашему региону.",
            reply_markup=reply_markup
        )
    
    async def handle_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        action = query.data
        
        # Логируем действие
        self.db.log_message(user_id, f"Кнопка: {action}", "callback")
        
        if action == "interest_cars":
            await self._handle_car_interest(query, context)
        elif action == "analyze_region":
            await self._handle_region_analysis(query, context)
        elif action == "get_offer":
            await self._handle_offer_request(query, context)
        elif action == "admin_export":
            await self._handle_admin_export(query, context)
        elif action == "export_excel":
            await self._handle_export_excel(query, context)
        elif action == "export_detailed":
            await self._handle_export_detailed(query, context)
    
    async def _handle_car_interest(self, query, context):
        """Обработка интереса к автомобилям"""
        user_id = query.from_user.id
        
        # Логируем интерес
        self.db.log_interest(user_id, "car_interest", "Общий интерес к автомобилям")
        
        keyboard = [
            [InlineKeyboardButton("🚙 Новые автомобили", callback_data="interest_new")],
            [InlineKeyboardButton("🚗 Подержанные автомобили", callback_data="interest_used")],
            [InlineKeyboardButton("⚡ Электромобили", callback_data="interest_electric")],
            [InlineKeyboardButton("📄 Получить КП", callback_data="get_offer")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Отлично! Какие автомобили вас интересуют?",
            reply_markup=reply_markup
        )
    
    async def _handle_region_analysis(self, query, context):
        """Запрос региона для анализа"""
        await query.edit_message_text(
            "🔍 Введите название вашего региона для анализа:\n\n"
            "Например:\n• Москва\n• Санкт-Петербург\n• Краснодарский край\n• Новосибирская область"
        )
        context.user_data['waiting_for_region'] = True
    
    async def _handle_offer_request(self, query, context):
        """Обработка запроса коммерческого предложения"""
        user_id = query.from_user.id
        
        # Проверяем, не получал ли уже пользователь предложение
        if self.db.has_received_offer(user_id):
            await query.edit_message_text(
                "📫 Вы уже получали наше коммерческое предложение.\n\n"
                "Для получения обновленного предложения или консультации "
                "свяжитесь с нашим менеджером: @manager_username"
            )
            return
        
        # Логируем запрос предложения
        self.db.log_interest(user_id, "offer_request", "Запрос коммерческого предложения")
        
        # Отправляем предложение
        await self._send_offer_pdf(user_id, context)
        
        # Логируем отправку
        self.db.log_offer_sent(user_id, "car_offer", "car_offer.pdf")
        
        await query.edit_message_text(
            "✅ Коммерческое предложение отправлено!\n\n"
            "В течение 24 часов с вами свяжется наш менеджер "
            "для уточнения деталей и ответа на вопросы."
        )
    
    async def _handle_admin_export(self, query, context):
        """Меню выгрузки для администратора"""
        keyboard = [
            [InlineKeyboardButton("📊 Excel отчет", callback_data="export_excel")],
            [InlineKeyboardButton("📋 Детальная выгрузка", callback_data="export_detailed")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📊 Выберите тип выгрузки данных:",
            reply_markup=reply_markup
        )
    
    async def _handle_export_excel(self, query, context):
        """Выгрузка Excel отчета"""
        await query.edit_message_text("🔄 Формирую Excel отчет... Это может занять несколько минут.")
        
        try:
            file_path = self.exporter.export_complete_report()
            
            if file_path:
                await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=open(file_path, 'rb'),
                    caption=f"📊 Полный отчет по клиентам\nСформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
            else:
                await query.edit_message_text("❌ Ошибка при формировании отчета.")
                
        except Exception as e:
            logger.error(f"Ошибка выгрузки: {e}")
            await query.edit_message_text("❌ Произошла ошибка при выгрузке данных.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Логируем сообщение
        self.db.log_message(user_id, message_text, "text")
        
        # Проверяем, ждем ли мы ввод региона
        if context.user_data.get('waiting_for_region'):
            await self._process_region_input(update, context, message_text)
            context.user_data['waiting_for_region'] = False
        else:
            # Обычное сообщение - предлагаем меню
            keyboard = [
                [InlineKeyboardButton("🚗 Автомобили", callback_data="interest_cars")],
                [InlineKeyboardButton("📊 Анализ региона", callback_data="analyze_region")],
                [InlineKeyboardButton("📄 КП", callback_data="get_offer")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Выберите опцию из меню:",
                reply_markup=reply_markup
            )
    
    async def _process_region_input(self, update, context, region: str):
        """Обработка введенного региона"""
        user_id = update.effective_user.id
        
        # Сохраняем регион
        self.db.update_user_region(user_id, region)
        self.db.log_interest(user_id, "region_analysis", region)
        
        # Анализируем регион с помощью AI
        analysis_msg = await update.message.reply_text(
            f"🔍 Анализирую регион {region}...\nЭто займет несколько секунд."
        )
        
        try:
            analysis = await self._analyze_region_with_ai(region)
            response = self._format_analysis_response(region, analysis)
            
            await analysis_msg.edit_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка анализа региона: {e}")
            await analysis_msg.edit_text(
                f"❌ Не удалось проанализировать регион {region}.\n"
                "Попробуйте позже или уточните название региона."
            )
    
    async def _analyze_region_with_ai(self, region: str) -> Dict:
        """Анализ региона с помощью OpenAI"""
        prompt = f"""
        Проанализируй регион {region} для продажи автомобилей и предоставь:
        
        1. Популярные Telegram каналы и чаты по тематике автомобилей (5-7 штук)
        2. Группы и сообщества по продаже автомобилей
        3. Потенциал рынка (высокий/средний/низкий)
        4. Примерное количество потенциальных клиентов
        5. Рекомендации по маркетингу
        
        Верни ответ в формате JSON:
        {{
            "telegram_channels": ["канал1", "канал2"],
            "chat_groups": ["группа1", "группа2"], 
            "market_potential": "высокий/средний/низкий",
            "potential_clients": число,
            "recommendations": "текст рекомендаций"
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def _format_analysis_response(self, region: str, analysis: Dict) -> str:
        """Форматирование ответа анализа"""
        channels = "\n".join([f"• {ch}" for ch in analysis.get('telegram_channels', [])[:5]])
        groups = "\n".join([f"• {gr}" for gr in analysis.get('chat_groups', [])[:5]])
        
        return (
            f"📊 Анализ региона: {region}\n\n"
            f"📈 Потенциал рынка: {analysis.get('market_potential', 'средний').upper()}\n"
            f"👥 Потенциальных клиентов: {analysis.get('potential_clients', 1000)}\n\n"
            f"📢 Рекомендуемые каналы:\n{channels}\n\n"
            f"💬 Рекомендуемые группы:\n{groups}\n\n"
            f"💡 Рекомендации:\n{analysis.get('recommendations', 'Стандартные рекомендации')}\n\n"
            f"🚗 Хотите получить коммерческое предложение?"
        )
    
    async def _send_offer_pdf(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Отправка PDF предложения"""
        try:
            # Получаем данные пользователя для персонализации
            user_messages = self.db.get_user_messages(user_id)
            user_interests = self.db.get_user_interests(user_id)
            
            # Генерируем персонализированное PDF
            pdf_path = self.pdf_gen.generate_offer(user_id, user_messages, user_interests)
            
            # Отправляем файл
            await context.bot.send_document(
                chat_id=user_id,
                document=open(pdf_path, 'rb'),
                caption=(
                    "🚗 Ваше коммерческое предложение по автомобилям\n\n"
                    "В предложении учтены ваши интересы и предпочтения. "
                    "Наш менеджер свяжется с вами для уточнения деталей!"
                )
            )
            
        except Exception as e:
            logger.error(f"Ошибка отправки PDF: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Извините, произошла ошибка при отправке предложения. Попробуйте позже."
            )

def main():
    """Запуск бота"""
    bot = CarSalesBot()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
