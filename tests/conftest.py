import os

# Секрет для проверки HMAC в тестах.
os.environ["WEBHOOK_SECRET"] = "test-secret"