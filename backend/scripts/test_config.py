from app.core.config import settings

print("=" * 50)
print("APPLICATION SETTINGS")
print("=" * 50)

print(f"Name        : {settings.app_name}")
print(f"Version     : {settings.app_version}")
print(f"Description : {settings.app_description}")

print()

print(f"Database    : {settings.database_url}")
print(f"Debug       : {settings.debug}")
print(f"Host        : {settings.host}")
print(f"Port        : {settings.port}")
