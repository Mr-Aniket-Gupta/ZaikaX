from django.db import models


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    keywords = models.CharField(max_length=500, blank=True, help_text="Comma-separated keywords")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question

    def keywords_list(self):
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]

    def matches(self, query: str) -> bool:
        q = (query or '').strip().lower()
        if not q:
            return True
        if q in self.question.lower() or q in self.answer.lower():
            return True
        for k in self.keywords_list():
            if k and (k in q or q in k):
                return True
        return False


class Review(models.Model):
    """Customer feedback/testimonial stored for display below the menu."""
    name = models.CharField(max_length=120)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)  # 1..5
    avatar_url = models.URLField(blank=True, null=True, help_text='Optional avatar image URL')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created",)
        verbose_name = "Customer Review"
        verbose_name_plural = "Customer Reviews"

    def __str__(self):
        return f"{self.name} — {self.rating}⭐"