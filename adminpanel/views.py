from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Dish
from menu.models import MenuItem
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from urllib.request import urlopen
from django.core.files.base import ContentFile
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
import datetime

# -------------------------
# ADMIN AUTHENTICATION
# -------------------------

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect("admin_dashboard")
        else:
            return render(request, "adminpanel/login.html", {
                "error": "Invalid credentials or not an admin!"
            })

    return render(request, "adminpanel/login.html")


def admin_logout(request):
    logout(request)
    return redirect("admin_login")

# -------------------------
# PROTECTED ADMIN PAGES
# -------------------------

@login_required(login_url="admin_login")
def dashboard(request):
    from cart.models import Order, OrderItem

    # Basic totals
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_menu_items = MenuItem.objects.count()

    # Order status counts
    status_counts = {s[0]: 0 for s in Order.STATUS_CHOICES}
    qs = Order.objects.values('status').annotate(count=Count('id'))
    for row in qs:
        status_counts[row['status']] = row['count']

    pending_orders = status_counts.get(Order.STATUS_PENDING, 0)
    completed_orders = status_counts.get(Order.STATUS_DELIVERED, 0)
    cancelled_orders = status_counts.get(Order.STATUS_CANCELLED, 0)

    # Top purchased items (by quantity and revenue)
    top_items_qs = (
        OrderItem.objects.values('item__id', 'item__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum(F('price_at_purchase') * F('quantity')))
        .order_by('-total_qty')[:3]
    )
    top_items = list(top_items_qs)

    # Top users by orders and spending
    top_users_qs = (
        Order.objects.values('user__id', 'user__username')
        .annotate(total_orders=Count('id'), total_spent=Sum('total_price'))
        .order_by('-total_spent')[:3]
    )
    top_users = list(top_users_qs)

    # Recent top 5 users by last order date
    recent_users = []
    from django.db.models import Max
    users_last = (
        Order.objects.values('user')
        .annotate(last_order=Max('created_at'))
        .order_by('-last_order')[:5]
    )
    for u in users_last:
        try:
            user_obj = User.objects.get(id=u['user'])
            last_order = Order.objects.filter(user=user_obj).order_by('-created_at').first()
            recent_users.append({
                'username': user_obj.username,
                'email': getattr(user_obj, 'email', ''),
                'last_order_date': last_order.created_at if last_order else None,
                'order_amount': last_order.total_price if last_order else 0,
            })
        except User.DoesNotExist:
            continue

    context = {
        'total_orders': total_orders,
        'total_users': total_users,
        'total_menu_items': total_menu_items,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'top_items': top_items,
        'top_users': top_users,
        'recent_users': recent_users,
    }

    return render(request, 'adminpanel/dashboard.html', context)


@login_required(login_url="admin_login")
def profile(request):
    """Allow admin to update their name/username/email and change password."""
    user = request.user
    if request.method == 'POST':
        # Basic profile updates
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        changed = False
        if username and username != user.username:
            # ensure uniqueness
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, 'Username already taken')
                return redirect('admin_profile')
            user.username = username
            changed = True
        if first_name is not None and first_name != user.first_name:
            user.first_name = first_name
            changed = True
        if last_name is not None and last_name != user.last_name:
            user.last_name = last_name
            changed = True
        if email is not None and email != user.email:
            user.email = email
            changed = True

        # Password change flow
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        if old_password or new_password1 or new_password2:
            # user intends to change password
            if not old_password:
                messages.error(request, 'Please enter your current password to change it')
                return redirect('admin_profile')
            if not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect')
                return redirect('admin_profile')
            if not new_password1 or not new_password2:
                messages.error(request, 'Please provide the new password twice')
                return redirect('admin_profile')
            if new_password1 != new_password2:
                messages.error(request, 'New passwords do not match')
                return redirect('admin_profile')
            # optional: add password validators; for now set directly
            user.set_password(new_password1)
            user.save()
            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully')
            return redirect('admin_profile')

        if changed:
            user.save()
            messages.success(request, 'Profile updated')
        else:
            messages.info(request, 'No changes made')

        return redirect('admin_profile')

    return render(request, 'adminpanel/profile.html', {'user': user})


@login_required(login_url="admin_login")
def sales_data(request):
    """Return JSON for sales chart. GET params: type=daily|monthly, range=int"""
    from cart.models import Order
    t = request.GET.get('type', 'daily')
    try:
        r = int(request.GET.get('range', 7))
    except ValueError:
        r = 7

    data = {'labels': [], 'data': []}
    now = timezone.now()
    if t == 'monthly':
        # last r months
        labels = []
        values = []
        for i in range(r - 1, -1, -1):
            month = (now - datetime.timedelta(days=30 * i)).replace(day=1)
            labels.append(month.strftime('%Y-%m'))
            start = month
            # approximate end of month
            end = (start + datetime.timedelta(days=32)).replace(day=1)
            total = Order.objects.filter(created_at__gte=start, created_at__lt=end).aggregate(s=Sum('total_price'))['s'] or 0
            values.append(float(total))
        data['labels'] = labels
        data['data'] = values
    else:
        # daily for last r days
        labels = []
        values = []
        for i in range(r - 1, -1, -1):
            day = (now - datetime.timedelta(days=i)).date()
            labels.append(day.strftime('%Y-%m-%d'))
            start = datetime.datetime.combine(day, datetime.time.min, tzinfo=timezone.get_current_timezone())
            end = datetime.datetime.combine(day, datetime.time.max, tzinfo=timezone.get_current_timezone())
            total = Order.objects.filter(created_at__gte=start, created_at__lte=end).aggregate(s=Sum('total_price'))['s'] or 0
            values.append(float(total))
        data['labels'] = labels
        data['data'] = values

    return JsonResponse(data)


@login_required(login_url="admin_login")
def menu_list(request):
    dishes = MenuItem.objects.all()
    return render(request, 'adminpanel/menu_list.html', {"dishes": dishes})


@login_required(login_url="admin_login")
def add_dish(request):
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        image = request.FILES.get('image')
        image_url = request.POST.get('image_url')

        item = MenuItem.objects.create(
            name=name,
            description=description,
            price=price,
            category=category
        )

        if image:
            item.image = image
            item.save()
        elif image_url:
            try:
                resp = urlopen(image_url)
                data = resp.read()
                filename = image_url.split('/')[-1].split('?')[0] or f"menu_{item.id}.jpg"
                item.image.save(filename, ContentFile(data))
            except Exception:
                pass

        return redirect('admin_menu')

    return render(request, 'adminpanel/add_dish.html')


@login_required(login_url="admin_login")
def edit_dish(request, id):
    dish = MenuItem.objects.get(id=id)
    if request.method == "POST":
        dish.name = request.POST.get('name')
        dish.description = request.POST.get('description')
        dish.price = request.POST.get('price')
        dish.category = request.POST.get('category')
        image = request.FILES.get('image')
        image_url = request.POST.get('image_url')
        if image:
            dish.image = image
        elif image_url:
            try:
                resp = urlopen(image_url)
                data = resp.read()
                filename = image_url.split('/')[-1].split('?')[0] or f"menu_{dish.id}.jpg"
                dish.image.save(filename, ContentFile(data))
            except Exception:
                pass
        dish.save()
        return redirect('admin_menu')

    return render(request, 'adminpanel/edit_dish.html', {"dish": dish})


# -------------------------
# EXTRA ADMIN PAGES
# -------------------------

@login_required(login_url="admin_login")
def orders(request):
    from cart.models import Order
    # support optional status filter via GET param
    status_filter = request.GET.get('status')
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    orders = orders.order_by('-created_at')
    # provide status choices for template
    status_choices = Order.STATUS_CHOICES
    return render(request, "adminpanel/orders.html", {"orders": orders, 'status_choices': status_choices})


@login_required(login_url="admin_login")
@require_POST
def update_order_status(request, order_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied")
        return redirect('admin_orders')
    from cart.models import Order
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    valid = [s[0] for s in Order.STATUS_CHOICES]
    if new_status in valid:
        order.status = new_status
        order.save()
        messages.success(request, f"Order {order.id} status updated to {new_status}")
    else:
        messages.error(request, "Invalid status")
    return redirect('admin_orders')


@login_required(login_url="admin_login")
def users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, "adminpanel/users.html", {"users": users})


@login_required(login_url="admin_login")
@require_POST
def assign_admin_assistant(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied")
        return redirect('admin_users')
    user = get_object_or_404(User, id=user_id)
    group, _ = Group.objects.get_or_create(name='Admin Assistant')
    user.groups.add(group)
    user.is_staff = True
    user.save()
    messages.success(request, f"{user.username} is now Admin Assistant")
    return redirect('admin_users')


@login_required(login_url="admin_login")
@require_POST
def remove_admin_assistant(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied")
        return redirect('admin_users')
    user = get_object_or_404(User, id=user_id)
    try:
        group = Group.objects.get(name='Admin Assistant')
        user.groups.remove(group)
    except Group.DoesNotExist:
        pass
    user.save()
    messages.success(request, f"Removed Admin Assistant role from {user.username}")
    return redirect('admin_users')


@login_required(login_url="admin_login")
@require_POST
def delete_dish(request, id):
    if not request.user.is_staff:
        # if AJAX request, return JSON error
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'permission_denied'}, status=403)
        messages.error(request, "Permission denied")
        return redirect('admin_menu')
    dish = get_object_or_404(MenuItem, id=id)
    dish.delete()
    # if AJAX request, return JSON for client-side handling
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'deleted', 'id': id})

    messages.success(request, "Dish deleted")
    return redirect('admin_menu')
