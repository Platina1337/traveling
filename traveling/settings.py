import os
from pathlib import Path

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development/debug
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # For production

# Настройки для SMTP сервера (раскомментировать для production)
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your_email@example.com'
# EMAIL_HOST_PASSWORD = 'your_email_password'

DEFAULT_FROM_EMAIL = 'noreply@travelingservice.com'
SERVER_EMAIL = 'server@travelingservice.com' 