from django.db import models
from django.conf import settings


class Address(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
	full_name = models.CharField(max_length=150)
	email = models.EmailField()
	phone = models.CharField(max_length=20)
	address_line1 = models.CharField(max_length=255)
	address_line2 = models.CharField(max_length=255, blank=True, null=True)
	city = models.CharField(max_length=100)
	state = models.CharField(max_length=100)
	pincode = models.CharField(max_length=20)
	country = models.CharField(max_length=100)
	is_default = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.full_name} - {self.address_line1}, {self.city}"
