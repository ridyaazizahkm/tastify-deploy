import os
import sys
import pytest
from django.conf import settings

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tastify.settings')
    import django
    django.setup()