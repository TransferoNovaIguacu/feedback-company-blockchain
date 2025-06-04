# feedback_platform/manage.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv  # Importa a função

def main():
    # Define a raiz do projeto
    BASE_DIR = Path(__file__).resolve().parent.parent  # Sobe UM nível!
    dotenv_path = BASE_DIR / 'blockchain' / '.env'
    load_dotenv(dotenv_path)

    # Configura as settings do Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedback_platform.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()