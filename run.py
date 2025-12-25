import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(port=int(os.environ.get("STACKOVERFLOW_API_PORT", 5000)))
