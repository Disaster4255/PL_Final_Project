import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frc_scouting.settings')
django.setup()

from django.contrib.auth.models import User, Group

# Create groups if they don't exist
admin_group, _ = Group.objects.get_or_create(name='Admin')
strategist_group, _ = Group.objects.get_or_create(name='Strategist')
scouter_group, _ = Group.objects.get_or_create(name='Scouter')

print("Groups created/verified: Admin, Strategist, Scouter")

# Create or update admin user
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True
    }
)
admin.set_password('admin123')
admin.save()

# Add to admin group
admin.groups.add(admin_group)

# Set admin role in profile
admin.profile.role = 'ADMIN'
admin.profile.save()

if created:
    print("✓ Admin user created")
else:
    print("✓ Admin user updated")

print("  Username: admin")
print("  Password: admin123")
print("  Role: ADMIN")
print("\nYou can now login at http://localhost:8000")
