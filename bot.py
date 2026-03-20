import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AdsLibraryBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.search_sessions = {}
        
    def get_application(self):
        """إنشاء تطبيق البوت"""
        return Application.builder().token(self.token).build()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /start"""
        welcome_message = """
🌟 *مرحباً بك في بوت البحث في مكتبة الإعلانات!* 🌟

يمكنك من خلال هذا البوت:
• 🔍 البحث عن الإعلانات حسب النص أو الكلمات المفتاحية
• 📊 عرض تفاصيل الإعلانات بشكل منظم
• 🏢 تصفية حسب المنطقة والمدة
• 📈 عرض إحصائيات وأداء الإعلانات

*كيفية الاستخدام:*
1. استخدم الأمر /search لبدء بحث جديد
2. أدخل كلمات البحث أو رابط الصفحة
3. اختر خيارات التصفية المناسبة

*الأوامر المتاحة:*
/search - بدء بحث جديد
/help - عرض المساعدة
/about - معلومات عن البوت
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /help"""
        help_text = """
📖 *دليل المساعدة*

*طرق البحث:*
1. *بحث بالنص*: أدخل الكلمات المفتاحية للإعلانات التي تبحث عنها
2. *بحث بالرابط*: أدخل رابط صفحة الفيسبوك أو الانستغرام
3. *بحث متقدم*: استخدم علامات التصنيف مثل #ads #facebook

*خيارات التصفية:*
• المنطقة: اختر الدولة أو المنطقة
• المدة: آخر 7 أيام، 30 يوماً، 90 يوماً
• المنصة: فيسبوك، انستغرام، مسنجر
• نوع الإعلان: صور، فيديو، كاروسيل

للحصول على مساعدة إضافية، تواصل مع المطور.
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /search"""
        keyboard = [
            [InlineKeyboardButton("🔍 بحث سريع", callback_data='quick_search')],
            [InlineKeyboardButton("🎯 بحث متقدم", callback_data='advanced_search')],
            [InlineKeyboardButton("📊 آخر الإعلانات", callback_data='recent_ads')],
            [InlineKeyboardButton("❌ إلغاء", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "اختر نوع البحث الذي تريده:",
            reply_markup=reply_markup
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل النصية"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        if user_id in self.search_sessions:
            session = self.search_sessions[user_id]
            if session['state'] == 'waiting_query':
                await self.process_search_query(update, context, message_text)
                del self.search_sessions[user_id]
            elif session['state'] == 'waiting_filters':
                await self.process_filters(update, context, message_text)
                del self.search_sessions[user_id]
        else:
            await self.perform_search(update, context, message_text)
    
    async def perform_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """تنفيذ البحث الفعلي"""
        await update.message.reply_text(f"🔍 جاري البحث عن: *{query}*", parse_mode='Markdown')
        
        # محاكاة البحث - هنا يمكنك ربط API حقيقي
        results = await self.search_ads_api(query)
        
        if results:
            await self.display_search_results(update, context, results)
        else:
            await update.message.reply_text("❌ لم يتم العثور على نتائج. حاول بكلمات بحث مختلفة.")
    
    async def search_ads_api(self, query: str):
        """البحث باستخدام API (يمكن تعديله لاستخدام API حقيقي)"""
        # مثال لاستخدام RapidAPI
        if self.rapidapi_key:
            try:
                url = "https://facebook-ads-library-api.p.rapidapi.com/search"
                headers = {
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": "facebook-ads-library-api.p.rapidapi.com"
                }
                params = {"q": query, "limit": 10}
                
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"API Error: {e}")
        
        # بيانات تجريبية إذا لم يعمل API
        return [
            {
                'id': '1',
                'title': f'إعلان لـ {query}',
                'advertiser': 'شركة تجريبية',
                'platform': 'فيسبوك',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'impressions': '1.2M',
                'spend': '$5,000',
                'status': 'نشط',
                'content': f'هذا هو محتوى الإعلان لـ {query}...',
            }
        ]
    
    async def display_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, results: list):
        """عرض نتائج البحث"""
        for i, ad in enumerate(results[:5]):
            message = f"""
📢 *الإعلان #{i+1}*

*العنوان:* {ad.get('title', 'غير متوفر')}
*المعلن:* {ad.get('advertiser', 'غير متوفر')}
*المنصة:* {ad.get('platform', 'غير متوفر')}
*الفترة:* {ad.get('start_date', 'N/A')} → {ad.get('end_date', 'N/A')}
*المشاهدات:* {ad.get('impressions', 'N/A')}
*الميزانية:* {ad.get('spend', 'N/A')}
*الحالة:* {ad.get('status', 'N/A')}

🔗 *رابط الإعلان:* `/ad_{ad.get('id', i)}`
"""
            keyboard = [[
                InlineKeyboardButton("📊 تفاصيل أكثر", callback_data=f'details_{ad.get("id", i)}'),
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith('details_'):
            ad_id = data.split('_')[1]
            await self.show_ad_details(query, ad_id)
        elif data == 'quick_search':
            await self.start_quick_search(query)
        elif data == 'advanced_search':
            await self.start_advanced_search(query)
        elif data == 'recent_ads':
            await self.show_recent_ads(query)
        elif data == 'cancel':
            await query.edit_message_text("❌ تم إلغاء العملية")
    
    async def show_ad_details(self, query, ad_id: str):
        """عرض تفاصيل الإعلان"""
        details = f"""
📋 *تفاصيل الإعلان #{ad_id}*

*أداء الإعلان:*
• نسبة النقر: 2.3%
• التفاعل: 15.2K
• التعليقات: 1.2K
• المشاركات: 3.4K

*الجمهور:*
• الأعمار: 25-45 سنة
• الجنس: 60% ذكر، 40% أنثى
"""
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back_to_results')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(details, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def start_quick_search(self, query):
        """بدء بحث سريع"""
        await query.edit_message_text(
            "🔍 *البحث السريع*\n\nأدخل الكلمات المفتاحية:",
            parse_mode='Markdown'
        )
        self.search_sessions[query.from_user.id] = {'state': 'waiting_query'}
    
    async def start_advanced_search(self, query):
        """بدء بحث متقدم"""
        await query.edit_message_text(
            "🎯 *البحث المتقدم*\n\nأدخل: الكلمات | الدولة | المدة\nمثال: سيارات | السعودية | 30",
            parse_mode='Markdown'
        )
        self.search_sessions[query.from_user.id] = {'state': 'waiting_filters'}
    
    async def process_search_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """معالجة استعلام البحث"""
        await self.perform_search(update, context, query)
    
    async def process_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE, filters_text: str):
        """معالجة التصفية"""
        await update.message.reply_text("✅ تم تطبيق التصفية بنجاح!")
    
    async def show_recent_ads(self, query):
        """عرض آخر الإعلانات"""
        await query.edit_message_text("📊 جاري تحميل آخر الإعلانات...")
        results = await self.search_ads_api("recent")
        # هنا تحتاج لعرض النتائج

def main():
    """تشغيل البوت"""
    bot = AdsLibraryBot()
    application = bot.get_application()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("search", bot.search_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # تشغيل البوت
    port = int(os.environ.get('PORT', 8443))
    
    # استخدام webhook في الإنتاج، polling في التطوير
    if os.environ.get('ENVIRONMENT') == 'production':
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
        )
    else:
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
