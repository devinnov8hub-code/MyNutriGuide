import pytest
from models import User

def test_password_hashing():
    u = User(first_name='Test', last_name='User', email='test@example.com')
    u.set_password('cat')
    assert u.check_password('cat')
    assert not u.check_password('dog')

def test_user_creation():
    u = User(first_name='Test', last_name='User', email='test@example.com')
    assert u.email == 'test@example.com'
    assert u.first_name == 'Test'
