from django.contrib import admin
from .models import MenuItem
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.core.files.base import ContentFile
from urllib.request import urlopen


class MenuItemAdminForm(forms.ModelForm):
	image_url = forms.URLField(required=False, help_text='Optional: paste an image URL to fetch')

	class Meta:
		model = MenuItem
		fields = ('name', 'description', 'price', 'category', 'image')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
	form = MenuItemAdminForm
	list_display = ('name', 'category', 'price', 'preview_image', 'delete_link')
	search_fields = ('name', 'category')

	def preview_image(self, obj):
		if obj.image:
			return format_html('<img src="{}" style="width:80px; height:50px; object-fit:cover; border-radius:6px;"/>', obj.image.url)
		return '-'
	preview_image.short_description = 'Image'

	def delete_link(self, obj):
		url = reverse('admin:menu_menuitem_delete', args=(obj.id,))
		return format_html('<a href="{}" style="color:#c62828">🗑️</a>', url)
	delete_link.short_description = 'Delete'

	def save_model(self, request, obj, form, change):
		# If admin provided image_url, fetch it and save to image field
		image_url = form.cleaned_data.get('image_url')
		if image_url and (not obj.image):
			try:
				resp = urlopen(image_url)
				img_data = resp.read()
				name = image_url.split('/')[-1].split('?')[0]
				if not name:
					name = f"menu_{obj.name}.jpg"
				obj.image.save(name, ContentFile(img_data), save=False)
			except Exception:
				# ignore fetch errors; admin can upload manually
				pass
		super().save_model(request, obj, form, change)
