from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from auditlog.registry import auditlog

class Notification(models.Model):
    user = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    # body = models.TextField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)  # optional meta
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification to {self.user.email}: {self.title}"


auditlog.register(Notification)