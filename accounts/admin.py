from django.contrib import admin
from .models import Address
from django.contrib.auth.models import User, Group
from django.contrib import admin as django_admin


# Actions to assign/remove Admin Assistant role
def make_admin_assistant(modeladmin, request, queryset):
	group, _ = Group.objects.get_or_create(name='Admin Assistant')
	for user in queryset:
		user.groups.add(group)
		user.is_staff = True
		user.save()


make_admin_assistant.short_description = "Make selected users Admin Assistant"


def remove_admin_assistant(modeladmin, request, queryset):
	try:
		group = Group.objects.get(name='Admin Assistant')
	except Group.DoesNotExist:
		group = None
	for user in queryset:
		if group:
			user.groups.remove(group)
		user.save()


remove_admin_assistant.short_description = "Remove Admin Assistant role from selected users"


# Replace default User admin to add our actions
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
try:
	django_admin.site.unregister(User)
except Exception:
	pass


@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):
	actions = [make_admin_assistant, remove_admin_assistant]
	list_display = ('username', 'email', 'is_staff', 'is_active', 'get_groups')

	def get_groups(self, obj):
		return ", ".join([g.name for g in obj.groups.all()])
	get_groups.short_description = 'Groups'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ('full_name', 'user', 'city', 'state', 'pincode', 'country', 'is_default')
	search_fields = ('full_name', 'user__username', 'city', 'pincode')
