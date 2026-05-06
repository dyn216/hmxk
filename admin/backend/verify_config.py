"""
简单验证脚本 - 避免Unicode问题
"""
from config import settings, get_settings, is_production, get_database_url
import os

print("=" * 50)
print("Configuration Module Verification")
print("=" * 50)

# Test basic configuration
print("\n[OK] App Name:", settings.app_name)
print("[OK] App Version:", settings.app_version)
print("[OK] Debug Mode:", settings.debug)

# Test server configuration
print("\n[OK] Server:", f"{settings.host}:{settings.port}")

# Test database configuration
print("\n[OK] Database URL:", get_database_url())

# Test JWT configuration
print("\n[OK] JWT Algorithm:", settings.jwt_algorithm)
print("[OK] JWT Expire Minutes:", settings.jwt_access_token_expire_minutes)

# Test log configuration
print("\n[OK] Log Level:", settings.log_level)
print("[OK] Log File:", settings.log_file)

# Test file upload configuration
print("\n[OK] Upload Max Size:", settings.upload_max_size / 1024 / 1024, "MB")
print("[OK] Allowed Extensions:", settings.upload_allowed_extensions)

# Test environment detection
print("\n[OK] Is Production:", is_production())

# Test directory creation
print("\nDirectory Check:")
directories = [
    os.path.dirname(settings.log_file),
    settings.upload_dir,
    settings.backup_dir
]

all_exist = True
for directory in directories:
    if directory and os.path.exists(directory):
        print(f"[OK] {directory}/ exists")
    else:
        print(f"[FAIL] {directory}/ does not exist")
        all_exist = False

print("\n" + "=" * 50)
if all_exist:
    print("All tests passed!")
else:
    print("Some tests failed!")
print("=" * 50)
