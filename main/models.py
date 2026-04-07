from django.conf import settings
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
        return [k.strip().lower() for k in self.keywords.split(",") if k.strip()]

    def matches(self, query: str) -> bool:
        q = (query or "").strip().lower()
        if not q:
            return True
        if q in self.question.lower() or q in self.answer.lower():
            return True
        for keyword in self.keywords_list():
            if keyword and (keyword in q or q in keyword):
                return True
        return False


class Review(models.Model):
    name = models.CharField(max_length=120)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    avatar_url = models.URLField(blank=True, null=True, help_text="Optional avatar image URL")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created",)
        verbose_name = "Customer Review"
        verbose_name_plural = "Customer Reviews"

    def __str__(self):
        return f"{self.name} - {self.rating} stars"


class RecipeShare(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_recipes",
    )
    title = models.CharField(max_length=180)
    short_description = models.CharField(max_length=240)
    story = models.TextField()
    ingredients = models.TextField(help_text="One ingredient per line")
    steps = models.TextField(help_text="One step per line")
    servings = models.PositiveIntegerField(default=2)
    prep_time_minutes = models.PositiveIntegerField(default=30)
    image_url = models.URLField(blank=True, null=True)
    allow_custom_orders = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Recipe Share"
        verbose_name_plural = "Recipe Shares"

    def __str__(self):
        return self.title

    @property
    def likes_count(self):
        return self.reactions.filter(reaction=RecipeReaction.REACTION_LIKE).count()

    @property
    def dislikes_count(self):
        return self.reactions.filter(reaction=RecipeReaction.REACTION_DISLIKE).count()

    @property
    def average_rating(self):
        result = self.reactions.exclude(rating__isnull=True).aggregate(avg=models.Avg("rating"))["avg"]
        return round(float(result or 0), 1)

    def ingredients_list(self):
        return [line.strip() for line in self.ingredients.splitlines() if line.strip()]

    def steps_list(self):
        return [line.strip() for line in self.steps.splitlines() if line.strip()]


class RecipeReaction(models.Model):
    REACTION_LIKE = "like"
    REACTION_DISLIKE = "dislike"
    REACTION_CHOICES = [
        (REACTION_LIKE, "Like"),
        (REACTION_DISLIKE, "Dislike"),
    ]

    recipe = models.ForeignKey(RecipeShare, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_reactions")
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        constraints = [
            models.UniqueConstraint(fields=["recipe", "user"], name="unique_recipe_reaction_per_user"),
        ]

    def __str__(self):
        return f"{self.user} -> {self.recipe}"


class RecipeOrderRequest(models.Model):
    STATUS_REQUESTED = "requested"
    STATUS_QUOTED = "quoted"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_REQUESTED, "Requested"),
        (STATUS_QUOTED, "Quoted"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
    ]

    PAYMENT_PENDING = "pending"
    PAYMENT_AWAITING = "awaiting"
    PAYMENT_PAID = "paid"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending Quote"),
        (PAYMENT_AWAITING, "Awaiting Payment"),
        (PAYMENT_PAID, "Paid"),
    ]

    recipe = models.ForeignKey(RecipeShare, on_delete=models.CASCADE, related_name="order_requests")
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipe_order_requests",
    )
    quantity = models.PositiveIntegerField(default=1)
    serving_note = models.CharField(max_length=160, blank=True)
    custom_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REQUESTED)
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_note = models.TextField(blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING,
    )
    quote_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Recipe Order Request"
        verbose_name_plural = "Recipe Order Requests"

    def __str__(self):
        return f"Recipe request {self.id} - {self.recipe.title}"
