from app import app, db
from models import User
from werkzeug.security import generate_password_hash

# Vytvoření kontextu aplikace
with app.app_context():
    # Kontrola, zda uživatel již existuje
    existing_user = User.query.filter_by(email='ondrej.klvac@smsreality.cz').first()
    
    if existing_user:
        print("Uživatel s tímto e-mailem již existuje.")
    else:
        # Vytvoření nového uživatele
        admin = User(
            email='ondrej.klvac@smsreality.cz',
            password=generate_password_hash('Reality1!'),
            first_name='Ondrej',
            last_name='Klvac',
            is_admin=True  # Pokud máte toto pole
        )
        
        # Přidání do databáze
        db.session.add(admin)
        db.session.commit()
        
        print("Admin uživatel byl úspěšně vytvořen!")