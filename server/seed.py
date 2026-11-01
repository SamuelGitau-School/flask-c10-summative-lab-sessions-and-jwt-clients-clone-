from faker import Faker

from app import app
from config import db
from models import Note, User

fake = Faker()
DEMO_PASSWORD = "password123"


def seed():
    Note.query.delete()
    User.query.delete()

    for username in ("alice", "bob", "carol"):
        user = User(username=username)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        for _ in range(25):  # enough to exercise pagination
            db.session.add(Note(
                title=fake.sentence(nb_words=4).rstrip("."),
                content=fake.paragraph(nb_sentences=3),
                user=user,
            ))
    db.session.commit()
    print(f"Seeded 3 users (password: {DEMO_PASSWORD}) with 25 notes each.")


if __name__ == "__main__":
    with app.app_context():
        seed()
