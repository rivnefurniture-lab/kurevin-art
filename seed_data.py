"""
Seed initial data for Kurevin Art Gallery
"""
from app import app, db, Admin, Painting
from werkzeug.security import generate_password_hash
import os

def seed_data():
    with app.app_context():
        db.create_all()
        
        # Create admin
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin')
            admin.set_password('kurevin2026')
            db.session.add(admin)
            print("Admin created: admin / kurevin2026")
        
        # Check if paintings already exist
        if Painting.query.count() > 0:
            print("Paintings already exist, skipping seed")
            db.session.commit()
            return
        
        # Paintings data based on files in the folder
        paintings_data = [
            {
                'title_uk': 'На Старокінці',
                'title_en': 'At Starokonka',
                'title_ru': 'На Староконке',
                'description_uk': 'Мальовничий куточок старої Одеси, де час ніби зупинився.',
                'description_en': 'A picturesque corner of old Odessa, where time seems to have stopped.',
                'description_ru': 'Живописный уголок старой Одессы, где время словно остановилось.',
                'width': 50,
                'height': 70,
                'year': 2023,
                'price': 1800,
                'image': 'At Starokonki.webp',
                'is_featured': True,
                'order': 1
            },
            {
                'title_uk': 'Узбережжя Чорного моря',
                'title_en': 'Coast of the Black Sea',
                'title_ru': 'Побережье Черного моря',
                'description_uk': 'Морський пейзаж з характерним для Одеси світлом та кольорами.',
                'description_en': 'Seascape with the light and colors characteristic of Odessa.',
                'description_ru': 'Морской пейзаж с характерным для Одессы светом и красками.',
                'width': 60,
                'height': 80,
                'year': 2024,
                'price': 2200,
                'image': 'Coast of the Black Sea.webp',
                'is_featured': True,
                'order': 2
            },
            {
                'title_uk': 'Французький бульвар',
                'title_en': 'French Boulevard',
                'title_ru': 'Французский бульвар',
                'description_uk': 'Один з найкрасивіших бульварів Одеси в сонячний день.',
                'description_en': 'One of the most beautiful boulevards of Odessa on a sunny day.',
                'description_ru': 'Один из красивейших бульваров Одессы в солнечный день.',
                'width': 50,
                'height': 60,
                'year': 2023,
                'price': 1600,
                'image': 'French Boulevard.webp',
                'is_featured': True,
                'order': 3
            },
            {
                'title_uk': 'Ранок',
                'title_en': 'Morning',
                'title_ru': 'Утро',
                'description_uk': 'Ніжне ранкове світло, що пробуджує місто.',
                'description_en': 'Gentle morning light awakening the city.',
                'description_ru': 'Нежный утренний свет, пробуждающий город.',
                'width': 40,
                'height': 50,
                'year': 2024,
                'price': 1200,
                'image': 'MORNING.webp',
                'is_featured': True,
                'order': 4
            },
            {
                'title_uk': 'Одеський дворик',
                'title_en': 'Odessa Courtyard',
                'title_ru': 'Одесский дворик',
                'description_uk': 'Типовий одеський дворик з його неповторною атмосферою.',
                'description_en': 'A typical Odessa courtyard with its unique atmosphere.',
                'description_ru': 'Типичный одесский дворик с его неповторимой атмосферой.',
                'width': 45,
                'height': 55,
                'year': 2023,
                'price': 1400,
                'image': 'Odessa Courtyard.webp',
                'is_featured': True,
                'order': 5
            },
            {
                'title_uk': 'Одеські півонії',
                'title_en': 'Odessa Peonies',
                'title_ru': 'Одесские пионы',
                'description_uk': 'Буяння кольорів та ароматів весняних квітів.',
                'description_en': 'A riot of colors and scents of spring flowers.',
                'description_ru': 'Буйство красок и ароматов весенних цветов.',
                'width': 50,
                'height': 60,
                'year': 2024,
                'price': 1500,
                'image': 'Odessa Peonies.webp',
                'is_featured': True,
                'order': 6
            },
        ]
        
        for data in paintings_data:
            # Check if image file exists
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], data['image'])
            if not os.path.exists(image_path):
                print(f"Warning: Image not found: {data['image']}")
                data['image'] = None
            
            painting = Painting(
                title_uk=data['title_uk'],
                title_en=data['title_en'],
                title_ru=data['title_ru'],
                description_uk=data['description_uk'],
                description_en=data['description_en'],
                description_ru=data['description_ru'],
                technique_uk='Олія на полотні',
                technique_en='Oil on canvas',
                technique_ru='Масло на холсте',
                width=data['width'],
                height=data['height'],
                year=data['year'],
                price=data['price'],
                image=data['image'],
                is_featured=data['is_featured'],
                order=data['order'],
                is_available=True,
                is_sold=False
            )
            db.session.add(painting)
            print(f"Added: {data['title_en']}")
        
        db.session.commit()
        print("\nSeed data complete!")
        print("Admin login: admin / kurevin2026")
        print(f"Total paintings: {Painting.query.count()}")

if __name__ == '__main__':
    seed_data()
