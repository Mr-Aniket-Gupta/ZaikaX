from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Dish
from cart.models import Coupon
from menu.models import Category, MenuItem, DEFAULT_CATEGORY_META
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from urllib.request import urlopen
from django.core.files.base import ContentFile
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper
from django.db.models.functions import ExtractWeekDay, TruncDay, TruncMonth
from django.utils import timezone
from django.utils.text import slugify
import datetime
from main.models import RecipeOrderRequest, RecipeShare


def _percent_change(current, previous):
    current = float(current or 0)
    previous = float(previous or 0)
    if previous == 0:
        if current == 0:
            return 0.0
        return 100.0
    return round(((current - previous) / previous) * 100, 1)


def _parse_datetime_local(value):
    if not value:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _dashboard_analytics(days=30):
    from cart.models import Order, OrderItem

    days = max(1, int(days))
    today = timezone.localdate()
    start_date = today - datetime.timedelta(days=days - 1)
    start_dt = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_dt = timezone.now()

    previous_start_dt = start_dt - datetime.timedelta(days=days)
    previous_end_dt = start_dt

    revenue_expr = ExpressionWrapper(
        F("price_at_purchase") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    orders_qs = Order.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
    prev_orders_qs = Order.objects.filter(created_at__gte=previous_start_dt, created_at__lt=previous_end_dt)

    revenue = orders_qs.aggregate(total=Sum("total_price"))["total"] or 0
    prev_revenue = prev_orders_qs.aggregate(total=Sum("total_price"))["total"] or 0
    total_orders = orders_qs.count()
    prev_total_orders = prev_orders_qs.count()
    active_customers = orders_qs.values("user").distinct().count()
    prev_active_customers = prev_orders_qs.values("user").distinct().count()
    average_order = (revenue / total_orders) if total_orders else 0
    prev_average_order = (prev_revenue / prev_total_orders) if prev_total_orders else 0
    discounts_given = orders_qs.aggregate(total=Sum("discount_amount"))["total"] or 0
    coupon_orders = orders_qs.exclude(applied_coupon__isnull=True).count()

    total_categories = Category.objects.count()
    total_items = MenuItem.objects.count()
    total_users = User.objects.count()
    veg_items = MenuItem.objects.filter(is_veg=True).count()
    non_veg_items = MenuItem.objects.filter(is_veg=False).count()

    delivered_orders = orders_qs.filter(status=Order.STATUS_DELIVERED).count()
    cancelled_orders = orders_qs.filter(status=Order.STATUS_CANCELLED).count()
    pending_orders = orders_qs.filter(status__in=[
        Order.STATUS_PENDING,
        Order.STATUS_PLACED,
        Order.STATUS_PROCESSING,
        Order.STATUS_SHIPPED,
    ]).count()
    repeat_customers = (
        orders_qs.values("user")
        .annotate(order_count=Count("id"))
        .filter(order_count__gte=2)
        .count()
    )
    items_sold = (
        OrderItem.objects.filter(order__created_at__gte=start_dt, order__created_at__lte=end_dt)
        .aggregate(total=Sum("quantity"))["total"] or 0
    )
    avg_items_per_order = (items_sold / total_orders) if total_orders else 0
    order_completion_rate = round((delivered_orders / total_orders) * 100, 1) if total_orders else 0
    cancellation_rate = round((cancelled_orders / total_orders) * 100, 1) if total_orders else 0
    repeat_customer_rate = round((repeat_customers / active_customers) * 100, 1) if active_customers else 0

    status_counts = {s[0]: 0 for s in Order.STATUS_CHOICES}
    for row in orders_qs.values("status").annotate(count=Count("id")):
        status_counts[row["status"]] = row["count"]

    day_rows = (
        orders_qs.annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(revenue=Sum("total_price"), orders=Count("id"))
        .order_by("day")
    )
    daily_lookup = {
        row["day"].date().isoformat(): {
            "revenue": float(row["revenue"] or 0),
            "orders": row["orders"],
        }
        for row in day_rows
    }

    labels = []
    revenue_series = []
    order_series = []
    for offset in range(days):
        current_day = start_date + datetime.timedelta(days=offset)
        key = current_day.isoformat()
        labels.append(current_day.strftime("%d %b"))
        revenue_series.append(daily_lookup.get(key, {}).get("revenue", 0))
        order_series.append(daily_lookup.get(key, {}).get("orders", 0))

    item_rows = (
        OrderItem.objects.filter(order__created_at__gte=start_dt, order__created_at__lte=end_dt)
        .values("item__id", "item__name")
        .annotate(total_qty=Sum("quantity"), total_revenue=Sum(revenue_expr))
        .order_by("-total_qty")[:5]
    )
    top_items = [
        {
            "name": row["item__name"],
            "qty": row["total_qty"],
            "revenue": float(row["total_revenue"] or 0),
        }
        for row in item_rows
    ]

    category_rows = (
        OrderItem.objects.filter(order__created_at__gte=start_dt, order__created_at__lte=end_dt)
        .values("item__category")
        .annotate(total_qty=Sum("quantity"), total_revenue=Sum(revenue_expr))
        .order_by("-total_qty")[:5]
    )
    top_categories = [
        {
            "slug": row["item__category"],
            "name": row["item__category"].replace("_", " ").title(),
            "qty": row["total_qty"],
            "revenue": float(row["total_revenue"] or 0),
        }
        for row in category_rows
    ]

    top_users_rows = (
        orders_qs.values("user__id", "user__username")
        .annotate(total_orders=Count("id"), total_spent=Sum("total_price"))
        .order_by("-total_spent")[:5]
    )
    top_users = [
        {
            "username": row["user__username"],
            "orders": row["total_orders"],
            "spent": float(row["total_spent"] or 0),
        }
        for row in top_users_rows
    ]

    city_rows = (
        orders_qs.values("city")
        .annotate(total_orders=Count("id"), revenue=Sum("total_price"))
        .order_by("-total_orders", "-revenue")[:6]
    )
    city_breakdown = [
        {
            "city": row["city"] or "Unknown",
            "orders": row["total_orders"],
            "revenue": float(row["revenue"] or 0),
        }
        for row in city_rows
    ]

    weekday_map = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
    weekday_rows = (
        orders_qs.annotate(weekday=ExtractWeekDay("created_at"))
        .values("weekday")
        .annotate(total_orders=Count("id"), revenue=Sum("total_price"))
        .order_by("weekday")
    )
    weekday_breakdown = [
        {
            "day": weekday_map.get(row["weekday"], str(row["weekday"])),
            "orders": row["total_orders"],
            "revenue": float(row["revenue"] or 0),
        }
        for row in weekday_rows
    ]

    low_item_rows = (
        OrderItem.objects.filter(order__created_at__gte=start_dt, order__created_at__lte=end_dt)
        .values("item__id", "item__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("total_qty", "item__name")[:5]
    )
    low_performing_items = [
        {"name": row["item__name"], "qty": row["total_qty"] or 0}
        for row in low_item_rows
    ]

    coupon_rows = (
        orders_qs.exclude(applied_coupon__isnull=True)
        .values("coupon_code")
        .annotate(total_orders=Count("id"), savings=Sum("discount_amount"))
        .order_by("-total_orders", "-savings")[:5]
    )
    coupon_usage = [
        {
            "code": row["coupon_code"],
            "orders": row["total_orders"],
            "savings": float(row["savings"] or 0),
        }
        for row in coupon_rows
    ]

    recent_orders = (
        orders_qs.select_related("user")
        .order_by("-created_at")[:6]
    )

    return {
        "days": days,
        "revenue": float(revenue or 0),
        "orders": total_orders,
        "active_customers": active_customers,
        "average_order": float(average_order or 0),
        "discounts_given": float(discounts_given or 0),
        "coupon_orders": coupon_orders,
        "total_categories": total_categories,
        "total_items": total_items,
        "total_users": total_users,
        "veg_items": veg_items,
        "non_veg_items": non_veg_items,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "pending_orders": pending_orders,
        "repeat_customers": repeat_customers,
        "items_sold": items_sold,
        "avg_items_per_order": round(float(avg_items_per_order or 0), 1),
        "order_completion_rate": order_completion_rate,
        "cancellation_rate": cancellation_rate,
        "repeat_customer_rate": repeat_customer_rate,
        "revenue_change": _percent_change(revenue, prev_revenue),
        "orders_change": _percent_change(total_orders, prev_total_orders),
        "active_customers_change": _percent_change(active_customers, prev_active_customers),
        "average_order_change": _percent_change(average_order, prev_average_order),
        "status_counts": status_counts,
        "labels": labels,
        "revenue_series": revenue_series,
        "order_series": order_series,
        "top_items": top_items,
        "top_categories": top_categories,
        "top_users": top_users,
        "city_breakdown": city_breakdown,
        "weekday_breakdown": weekday_breakdown,
        "low_performing_items": low_performing_items,
        "coupon_usage": coupon_usage,
        "recent_orders": list(recent_orders),
    }

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

    analytics = _dashboard_analytics(30)

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
        'dashboard_analytics': analytics,
    }

    return render(request, 'adminpanel/dashboard.html', context)


@login_required(login_url="admin_login")
def dashboard_analytics_data(request):
    try:
        days = int(request.GET.get("days", 30))
    except ValueError:
        days = 30

    analytics = _dashboard_analytics(days)
    payload = {
        "days": analytics["days"],
        "revenue": analytics["revenue"],
        "orders": analytics["orders"],
        "active_customers": analytics["active_customers"],
        "average_order": analytics["average_order"],
        "discounts_given": analytics["discounts_given"],
        "coupon_orders": analytics["coupon_orders"],
        "total_categories": analytics["total_categories"],
        "total_items": analytics["total_items"],
        "total_users": analytics["total_users"],
        "veg_items": analytics["veg_items"],
        "non_veg_items": analytics["non_veg_items"],
        "delivered_orders": analytics["delivered_orders"],
        "cancelled_orders": analytics["cancelled_orders"],
        "pending_orders": analytics["pending_orders"],
        "repeat_customers": analytics["repeat_customers"],
        "items_sold": analytics["items_sold"],
        "avg_items_per_order": analytics["avg_items_per_order"],
        "order_completion_rate": analytics["order_completion_rate"],
        "cancellation_rate": analytics["cancellation_rate"],
        "repeat_customer_rate": analytics["repeat_customer_rate"],
        "revenue_change": analytics["revenue_change"],
        "orders_change": analytics["orders_change"],
        "active_customers_change": analytics["active_customers_change"],
        "average_order_change": analytics["average_order_change"],
        "status_counts": analytics["status_counts"],
        "labels": analytics["labels"],
        "revenue_series": analytics["revenue_series"],
        "order_series": analytics["order_series"],
        "top_items": analytics["top_items"],
        "top_categories": analytics["top_categories"],
        "top_users": analytics["top_users"],
        "city_breakdown": analytics["city_breakdown"],
        "weekday_breakdown": analytics["weekday_breakdown"],
        "low_performing_items": analytics["low_performing_items"],
        "coupon_usage": analytics["coupon_usage"],
        "recent_orders": [
            {
                "id": order.id,
                "user": order.user.username,
                "status": order.status,
                "total": float(order.total_price or 0),
                "created_at": timezone.localtime(order.created_at).strftime("%d %b %Y, %I:%M %p"),
            }
            for order in analytics["recent_orders"]
        ],
    }
    return JsonResponse(payload)


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


def _category_choices():
    return Category.objects.all()


@login_required(login_url="admin_login")
def category_list(request):
    categories = Category.objects.all()
    category_usage = {
        row["category"]: row["count"]
        for row in MenuItem.objects.values("category").annotate(count=Count("id"))
    }
    return render(
        request,
        "adminpanel/categories.html",
        {
            "categories": categories,
            "category_usage": category_usage,
        },
    )


@login_required(login_url="admin_login")
@require_POST
def add_category(request):
    name = (request.POST.get("name") or "").strip()
    slug = slugify((request.POST.get("slug") or "").strip() or name)
    icon = (request.POST.get("icon") or "🍽").strip() or "🍽"
    display_order = request.POST.get("display_order") or "100"

    if not name:
        messages.error(request, "Category name is required.")
        return redirect("admin_categories")

    if not slug:
        messages.error(request, "A valid category slug is required.")
        return redirect("admin_categories")

    if Category.objects.filter(slug=slug).exists():
        messages.error(request, "A category with that slug already exists.")
        return redirect("admin_categories")

    Category.objects.create(
        name=name,
        slug=slug,
        icon=icon,
        display_order=int(display_order),
    )
    messages.success(request, f"Category '{name}' created.")
    return redirect("admin_categories")


@login_required(login_url="admin_login")
@require_POST
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    old_slug = category.slug

    name = (request.POST.get("name") or "").strip()
    slug = slugify((request.POST.get("slug") or "").strip() or name)
    icon = (request.POST.get("icon") or "🍽").strip() or "🍽"
    display_order = request.POST.get("display_order") or category.display_order

    if not name or not slug:
        messages.error(request, "Category name and slug are required.")
        return redirect("admin_categories")

    if Category.objects.filter(slug=slug).exclude(id=category.id).exists():
        messages.error(request, "Another category already uses that slug.")
        return redirect("admin_categories")

    category.name = name
    category.slug = slug
    category.icon = icon
    category.display_order = int(display_order)
    category.save()

    if old_slug != slug:
        MenuItem.objects.filter(category=old_slug).update(category=slug)

    messages.success(request, f"Category '{name}' updated.")
    return redirect("admin_categories")


@login_required(login_url="admin_login")
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    linked_items = MenuItem.objects.filter(category=category.slug).count()
    if linked_items:
        messages.error(request, f"Cannot delete '{category.name}' because {linked_items} dishes still use it.")
        return redirect("admin_categories")

    category.delete()
    messages.success(request, "Category deleted.")
    return redirect("admin_categories")


@login_required(login_url="admin_login")
def add_dish(request):
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        image = request.FILES.get('image')
        image_url = request.POST.get('image_url')

        if not Category.objects.filter(slug=category).exists():
            messages.error(request, "Please select a valid category.")
            return redirect('add_dish')

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

    return render(request, 'adminpanel/add_dish.html', {"categories": _category_choices()})


@login_required(login_url="admin_login")
def edit_dish(request, id):
    dish = MenuItem.objects.get(id=id)
    if request.method == "POST":
        dish.name = request.POST.get('name')
        dish.description = request.POST.get('description')
        dish.price = request.POST.get('price')
        dish.category = request.POST.get('category')
        if not Category.objects.filter(slug=dish.category).exists():
            messages.error(request, "Please select a valid category.")
            return redirect('edit_dish', id=id)
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

    return render(request, 'adminpanel/edit_dish.html', {"dish": dish, "categories": _category_choices()})


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
def offers(request):
    coupons = Coupon.objects.all().order_by("-created_at")
    return render(request, "adminpanel/offers.html", {"coupons": coupons})


@login_required(login_url="admin_login")
@require_POST
def add_offer(request):
    code = (request.POST.get("code") or "").strip().upper()
    if not code:
        messages.error(request, "Coupon code is required.")
        return redirect("admin_offers")

    if Coupon.objects.filter(code=code).exists():
        messages.error(request, "Coupon code already exists.")
        return redirect("admin_offers")

    valid_until = _parse_datetime_local(request.POST.get("valid_until"))
    Coupon.objects.create(
        code=code,
        title=(request.POST.get("title") or "").strip() or code,
        description=(request.POST.get("description") or "").strip(),
        discount_type=request.POST.get("discount_type") or Coupon.DISCOUNT_PERCENT,
        discount_value=request.POST.get("discount_value") or 0,
        min_order_amount=request.POST.get("min_order_amount") or 0,
        max_discount_amount=request.POST.get("max_discount_amount") or None,
        usage_limit=request.POST.get("usage_limit") or None,
        per_user_limit=request.POST.get("per_user_limit") or 1,
        valid_until=valid_until,
        is_active=bool(request.POST.get("is_active")),
    )
    messages.success(request, f"Offer {code} created.")
    return redirect("admin_offers")


@login_required(login_url="admin_login")
@require_POST
def update_offer(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.code = (request.POST.get("code") or coupon.code).strip().upper()
    coupon.title = (request.POST.get("title") or coupon.title).strip()
    coupon.description = (request.POST.get("description") or "").strip()
    coupon.discount_type = request.POST.get("discount_type") or coupon.discount_type
    coupon.discount_value = request.POST.get("discount_value") or coupon.discount_value
    coupon.min_order_amount = request.POST.get("min_order_amount") or 0
    coupon.max_discount_amount = request.POST.get("max_discount_amount") or None
    coupon.usage_limit = request.POST.get("usage_limit") or None
    coupon.per_user_limit = request.POST.get("per_user_limit") or 1
    coupon.valid_until = _parse_datetime_local(request.POST.get("valid_until"))
    coupon.is_active = bool(request.POST.get("is_active"))
    coupon.save()
    messages.success(request, f"Offer {coupon.code} updated.")
    return redirect("admin_offers")


@login_required(login_url="admin_login")
@require_POST
def delete_offer(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, "Offer deleted.")
    return redirect("admin_offers")


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
def recipe_shares(request):
    recipes = RecipeShare.objects.select_related("author").all()
    return render(
        request,
        "adminpanel/recipes.html",
        {
            "recipes": recipes,
            "total_recipes": recipes.count(),
            "open_custom_orders": recipes.filter(allow_custom_orders=True).count(),
        },
    )


@login_required(login_url="admin_login")
def recipe_order_requests(request):
    requests_qs = RecipeOrderRequest.objects.select_related("recipe", "requester", "recipe__author").all()
    status_filter = request.GET.get("status")
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    return render(
        request,
        "adminpanel/recipe_orders.html",
        {
            "recipe_requests": requests_qs,
            "status_choices": RecipeOrderRequest.STATUS_CHOICES,
        },
    )


@login_required(login_url="admin_login")
@require_POST
def update_recipe_order_request(request, request_id):
    recipe_request = get_object_or_404(RecipeOrderRequest, id=request_id)
    status = request.POST.get("status") or recipe_request.status
    valid_statuses = {choice[0] for choice in RecipeOrderRequest.STATUS_CHOICES}
    if status not in valid_statuses:
        messages.error(request, "Invalid recipe request status.")
        return redirect("admin_recipe_orders")

    quoted_price = (request.POST.get("quoted_price") or "").strip()
    recipe_request.admin_note = (request.POST.get("admin_note") or "").strip()
    recipe_request.status = status

    if quoted_price:
        recipe_request.quoted_price = quoted_price
        recipe_request.payment_status = RecipeOrderRequest.PAYMENT_AWAITING
        recipe_request.quote_sent_at = timezone.now()
        if recipe_request.status == RecipeOrderRequest.STATUS_REQUESTED:
            recipe_request.status = RecipeOrderRequest.STATUS_QUOTED

    if recipe_request.status == RecipeOrderRequest.STATUS_COMPLETED:
        recipe_request.payment_status = RecipeOrderRequest.PAYMENT_PAID

    if recipe_request.status == RecipeOrderRequest.STATUS_REJECTED:
        recipe_request.payment_status = RecipeOrderRequest.PAYMENT_PENDING

    recipe_request.save()
    messages.success(request, f"Recipe request #{recipe_request.id} updated.")
    return redirect("admin_recipe_orders")


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
