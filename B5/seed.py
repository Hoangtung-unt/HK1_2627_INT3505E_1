from app import create_app
from models import db, Book

app = create_app()

def seed_data():
    with app.app_context():
        # Reset lại cơ sở dữ liệu
        db.drop_all()
        db.create_all()

        genres = ["tech", "novel", "science", "history"]
        books = []
        
        for i in range(1, 51):
            book = Book(
                title=f"Sách Lập trình & Thiết kế Hệ thống Tập {i}",
                isbn=f"9786040000{i:02d}",
                price_vnd=100000 + (i * 10000),
                stock=15 + (i % 5),
                genre=genres[i % len(genres)]
            )
            books.append(book)
            
        db.session.add_all(books)
        db.session.commit()
        print(" Đã nạp thành công 50 cuốn sách mẫu vào Database!")

if __name__ == "__main__":
    seed_data()