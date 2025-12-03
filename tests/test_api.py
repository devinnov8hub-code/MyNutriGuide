import pytest
from app import create_app, db
from models import User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test user
            u = User(first_name='Test', last_name='User', email='test@example.com')
            u.set_password('password')
            db.session.add(u)
            db.session.commit()
            
        yield client

def test_upload_no_auth(client):
    response = client.post('/api/upload', json={'image_data': 'fake'})
    assert response.status_code == 401

def test_upload_bad_payload(client):
    # Login first
    client.post('/login', data={'email': 'test@example.com', 'password': 'password'})
    
    response = client.post('/api/upload', json={})
    assert response.status_code == 400
