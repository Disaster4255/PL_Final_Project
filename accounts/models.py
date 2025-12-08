from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    """
    Extended user profile with role-based permissions
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('STRATEGIST', 'Strategist'),
        ('SCOUTER', 'Scouter'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SCOUTER')
    
    # Gamification fields
    prediction_points = models.IntegerField(default=0)
    experience_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_strategist(self):
        return self.role == 'STRATEGIST'
    
    def is_scouter(self):
        return self.role == 'SCOUTER'
    
    def can_manage_users(self):
        return self.role == 'ADMIN'
    
    def can_manage_events(self):
        return self.role in ['ADMIN', 'STRATEGIST']
    
    def can_assign_scouters(self):
        return self.role in ['ADMIN', 'STRATEGIST']
    
    def can_view_analytics(self):
        return True  # All roles can view analytics
    
    def add_prediction_point(self):
        self.prediction_points += 1
        self.save()
    
    def add_experience(self, points):
        self.experience_points += points
        # Level up every 100 XP
        new_level = (self.experience_points // 100) + 1
        if new_level > self.level:
            self.level = new_level
            # Award achievement badge
            Achievement.objects.create(
                user_profile=self,
                badge_type='LEVEL',
                description=f'Reached Level {new_level}',
                level_achieved=new_level
            )
        self.save()


class Achievement(models.Model):
    """
    Achievement badges for gamification
    """
    BADGE_TYPES = [
        ('LEVEL', 'Level Up'),
        ('PREDICTION', 'Prediction Master'),
        ('REPORTS', 'Report Champion'),
        ('ACCURACY', 'Data Accuracy'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='achievements')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    description = models.CharField(max_length=200)
    level_achieved = models.IntegerField(null=True, blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.get_badge_type_display()}: {self.description}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a User is created
    """
    if created:
        UserProfile.objects.create(user=instance)
