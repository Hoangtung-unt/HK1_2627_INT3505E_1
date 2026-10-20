import pytest
from app import create_app
from models import db, Book

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        for i in range(1, 35):
            b = Book(
                title=f"Sách Test {i}",
                isbn=f"9786040000{i:02d}",
                price_vnd=100000 + i * 5000,
                stock=10,
                genre="tech" if i % 2 == 0 else "novel"
            )
            db.session.add(b)
        db.session.commit()
        yield app.test_client()
        db.drop_all()

def test_offset_pagination(client):
    res = client.get("/api/v1/books?strategy=offset&offset=0&limit=5&genre=tech")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) == 5
    assert data["pagination"]["strategy"] == "offset"

def test_cursor_pagination_and_multisort(client):
    res = client.get("/api/v1/books?strategy=cursor&limit=5&sort=-price,title&genre=tech")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) == 5
    assert data["pagination"]["strategy"] == "cursor"
    
    next_c = data["pagination"]["next_cursor"]
    if next_c:
        res2 = client.get(f"/api/v1/books?strategy=cursor&limit=5&sort=-price,title&genre=tech&cursor={next_c}")
        assert res2.status_code == 200
        assert len(res2.get_json()["data"]) > 0

def test_bad_sort_whitelist_rejection(client):
    res = client.get("/api/v1/books?sort=invalid_column")
    assert res.status_code == 400
    assert res.get_json()["error"] == "bad_sort"