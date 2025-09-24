import pytest
from app import app, db, User, Expense

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def register(client, username, email, password):
    return client.post('/register', data=dict(username=username, email=email, password=password), follow_redirects=True)

def login(client, email, password):
    return client.post('/login', data=dict(email=email, password=password), follow_redirects=True)

def test_register_login(client):
    rv = register(client, 'testuser', 'test@example.com', 'password123')
    assert b'Account created' in rv.data
    rv = login(client, 'test@example.com', 'password123')
    assert b'Logged in successfully' in rv.data

def test_add_expense(client):
    register(client, 'testuser', 'test@example.com', 'password123')
    login(client, 'test@example.com', 'password123')
    rv = client.post('/add', data=dict(date='2025-09-24', category='Food', amount='50', note='Lunch'), follow_redirects=True)
    assert b'Expense added' in rv.data
    assert Expense.query.count() == 1
