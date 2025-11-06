from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import os

class PDFGenerator:
    def __init__(self, output_dir: str = "offers"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_offer(self, user_id: int, messages: list, interests: list) -> str:
        """Генерация персонализированного коммерческого предложения"""
        filename = f"{self.output_dir}/offer_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        
        # Заголовок
        title = Paragraph("КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Информация о клиенте
        client_info = Paragraph(
            f"Сформировано для клиента ID: {user_id}<br/>"
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            styles['Normal']
        )
        story.append(client_info)
        story.append(Spacer(1, 20))
        
        # Учет интересов клиента
        if interests:
            interests_text = "Учтенные интересы клиента:<br/>" + "<br/>".join(
                [f"• {interest['type']}: {interest['details']}" for interest in interests[:5]]
            )
            story.append(Paragraph(interests_text, styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Основное предложение
        offer_text = """
        <b>Специальное предложение по автомобилям</b><br/><br/>
        
        • Широкий выбор новых и подержанных автомобилей<br/>
        • Выгодные условия кредитования<br/>
        • Trade-in вашего автомобиля<br/>
        • Полное сопровождение сделки<br/>
        • Гарантия на все автомобили<br/><br/>
        
        <b>Преимущества:</b><br/>
        ✓ Лучшие цены на рынке<br/>
        ✓ Проверенная история автомобилей<br/>
        ✓ Юридическое сопровождение<br/>
        ✓ Доставка по региону<br/>
        """
        
        story.append(Paragraph(offer_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Контактная информация
        contacts = Paragraph(
            "<b>Контактная информация:</b><br/>"
            "Телефон: +7 (XXX) XXX-XX-XX<br/>"
            "Telegram: @car_sales_manager<br/>"
            "Email: info@carsales.ru<br/><br/>"
            
            "Мы свяжемся с вами в течение 24 часов!",
            styles['Normal']
        )
        story.append(contacts)
        
        doc.build(story)
        return filename
