from django.db import models
from auditlog.registry import auditlog

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)
    priority = models.CharField(
        choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        max_length=10
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class FileUpload(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        related_name='files',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to='announcements/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.id} - {self.file.name}'


auditlog.register(Announcement)
auditlog.register(FileUpload)
