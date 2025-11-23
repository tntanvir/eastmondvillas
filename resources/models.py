from django.db import models


class Resource(models.Model):

    CATEGORY_CHOICES = [
        ("branding", "Branding"),
        ("templates", "Templates"),
        ("legal_forms", "Legal Forms"),
        ("training", "Training"),
        ("market_research", "Market Research"),
        ("external_tools", "External Tools"),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )
    description = models.TextField()
    file = models.FileField(upload_to='resources/')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
