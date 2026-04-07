from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from accounts.forms import RegistrationForm, UserProfileForm, AddressForm
from accounts.models import Address
from cart.models import Order
import random
from menu.models import Category, MenuItem
from .recommendations import get_personalized_recommendations
from .models import FAQ, RecipeOrderRequest, RecipeReaction, RecipeShare


def _safe_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default

# Pages
def index(request):
    categories = []
    for category in Category.objects.all():
        category_items = MenuItem.objects.filter(category=category.slug)
        if not category_items.exists():
            continue

        category_image_item = (
            category_items.exclude(image__isnull=True)
            .exclude(image='')
            .order_by('?')
            .first()
        ) or category_items.order_by('?').first()

        categories.append({
            'key': category.slug,
            'label': category.name,
            'count': category_items.count(),
            'image_item': category_image_item,
            'icon': category.icon or '🍽',
            'menu_anchor': category.slug.replace('_', '-'),
        })

    random.shuffle(categories)
    homepage_categories = categories[:4]

    popular_dishes = list(
        MenuItem.objects.exclude(image__isnull=True)
        .exclude(image='')
        .order_by('?')[:3]
    )

    if len(popular_dishes) < 3:
        existing_ids = {item.id for item in popular_dishes}
        fallback_items = MenuItem.objects.exclude(id__in=existing_ids).order_by('?')[: 3 - len(popular_dishes)]
        popular_dishes.extend(list(fallback_items))

    context = {
        'homepage_categories': homepage_categories,
        'popular_dishes': popular_dishes,
        'recommendations': get_personalized_recommendations(request.user, limit=4),
    }
    return render(request, 'main/index.html', context)

def menu_list(request):
    return render(request, 'main/menu_list.html')

def about(request):
    return render(request, 'main/about.html')

def contact(request):
    return render(request, 'main/contact.html')


def recipes(request):
    recipe_list = RecipeShare.objects.filter(is_published=True).select_related("author")
    top_recipes = recipe_list[:3]
    user_requests = []
    if request.user.is_authenticated:
        user_requests = RecipeOrderRequest.objects.filter(requester=request.user).select_related("recipe")[:5]

    context = {
        "recipes": recipe_list,
        "top_recipes": top_recipes,
        "user_recipe_requests": user_requests,
    }
    return render(request, "main/recipes.html", context)


@login_required(login_url="login")
def share_recipe(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        short_description = (request.POST.get("short_description") or "").strip()
        story = (request.POST.get("story") or "").strip()
        ingredients = (request.POST.get("ingredients") or "").strip()
        steps = (request.POST.get("steps") or "").strip()
        image_url = (request.POST.get("image_url") or "").strip()

        if not all([title, short_description, story, ingredients, steps]):
            messages.error(request, "Please fill in all recipe details before sharing.")
            return redirect("share_recipe")

        RecipeShare.objects.create(
            author=request.user,
            title=title,
            short_description=short_description,
            story=story,
            ingredients=ingredients,
            steps=steps,
            servings=_safe_positive_int(request.POST.get("servings"), 2),
            prep_time_minutes=max(_safe_positive_int(request.POST.get("prep_time_minutes"), 30), 5),
            image_url=image_url or None,
            allow_custom_orders=bool(request.POST.get("allow_custom_orders")),
            is_published=True,
        )
        messages.success(request, "Your recipe is live now and other food lovers can explore it.")
        return redirect("recipes")

    return render(request, "main/recipe_share.html")


def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(
        RecipeShare.objects.filter(is_published=True).select_related("author"),
        id=recipe_id,
    )
    user_reaction = None
    if request.user.is_authenticated:
        user_reaction = RecipeReaction.objects.filter(recipe=recipe, user=request.user).first()

    similar_recipes = RecipeShare.objects.filter(is_published=True).exclude(id=recipe.id)[:4]
    recent_requests = recipe.order_requests.select_related("requester")[:6]

    context = {
        "recipe": recipe,
        "user_reaction": user_reaction,
        "similar_recipes": similar_recipes,
        "recent_requests": recent_requests,
    }
    return render(request, "main/recipe_detail.html", context)


@login_required(login_url="login")
@require_POST
def react_to_recipe(request, recipe_id):
    recipe = get_object_or_404(RecipeShare, id=recipe_id, is_published=True)
    reaction_value = (request.POST.get("reaction") or "").strip()
    rating_value = request.POST.get("rating")

    reaction, _ = RecipeReaction.objects.get_or_create(recipe=recipe, user=request.user)

    if reaction_value in {RecipeReaction.REACTION_LIKE, RecipeReaction.REACTION_DISLIKE}:
        reaction.reaction = reaction_value

    if rating_value:
        try:
            rating_int = int(rating_value)
        except ValueError:
            rating_int = None
        if rating_int and 1 <= rating_int <= 5:
            reaction.rating = rating_int

    reaction.save()
    messages.success(request, "Your feedback has been saved for this recipe.")
    return redirect("recipe_detail", recipe_id=recipe.id)


@login_required(login_url="login")
@require_POST
def request_recipe_order(request, recipe_id):
    recipe = get_object_or_404(RecipeShare, id=recipe_id, is_published=True)
    if not recipe.allow_custom_orders:
        messages.error(request, "This recipe is shared for inspiration only right now.")
        return redirect("recipe_detail", recipe_id=recipe.id)

    quantity = _safe_positive_int(request.POST.get("quantity"), 1)
    RecipeOrderRequest.objects.create(
        recipe=recipe,
        requester=request.user,
        quantity=quantity,
        serving_note=(request.POST.get("serving_note") or "").strip(),
        custom_notes=(request.POST.get("custom_notes") or "").strip(),
    )
    messages.success(request, "Custom order request sent. Admin will review and share the final amount with you.")
    return redirect("recipe_detail", recipe_id=recipe.id)


@login_required(login_url="login")
def my_recipe_orders(request):
    requests_qs = RecipeOrderRequest.objects.filter(requester=request.user).select_related("recipe", "recipe__author")
    return render(request, "main/recipe_orders.html", {"recipe_orders": requests_qs})


@login_required(login_url="login")
@require_POST
def accept_recipe_quote(request, request_id):
    recipe_request = get_object_or_404(RecipeOrderRequest, id=request_id, requester=request.user)
    if not recipe_request.quoted_price:
        messages.error(request, "Quote is not ready yet.")
        return redirect("my_recipe_orders")

    recipe_request.status = RecipeOrderRequest.STATUS_APPROVED
    recipe_request.payment_status = RecipeOrderRequest.PAYMENT_AWAITING
    recipe_request.save(update_fields=["status", "payment_status", "updated_at"])
    messages.success(
        request,
        "Quote accepted. Our team will contact you for payment and preparation confirmation.",
    )
    return redirect("my_recipe_orders")


# AUTH
def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')

    return render(request, 'main/login.html')

def generate_otp():
    return str(random.randint(100000, 999999))


def register_user(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # Create address record
            Address.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address_line1=form.cleaned_data['address_line1'],
                address_line2=form.cleaned_data.get('address_line2',''),
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                pincode=form.cleaned_data['pincode'],
                country=form.cleaned_data['country'],
                is_default=True,
            )
            messages.success(request, "Account created successfully. Please login.")
            return redirect('login')
        else:
            return render(request, 'main/register.html', {'form': form})

    # For GET and other methods, render an empty registration form
    form = RegistrationForm()
    return render(request, 'main/register.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def user_profile(request):
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    profile_form = UserProfileForm(instance=request.user)
    address_form = AddressForm(initial={
        'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'email': request.user.email,
    })

    edit_address = None
    edit_address_form = None
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_address = get_object_or_404(Address, id=edit_id, user=request.user)
        edit_address_form = AddressForm(instance=edit_address)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = UserProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('user_profile')
            messages.error(request, 'Please fix profile form errors.')

        elif form_type == 'address_add':
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                new_address = address_form.save(commit=False)
                new_address.user = request.user
                if not addresses.exists():
                    new_address.is_default = True
                new_address.save()

                if new_address.is_default:
                    Address.objects.filter(user=request.user).exclude(id=new_address.id).update(is_default=False)

                messages.success(request, 'Address added successfully.')
                return redirect('user_profile')
            messages.error(request, 'Please fix address form errors.')

        elif form_type == 'address_edit':
            address_id = request.POST.get('address_id')
            edit_address = get_object_or_404(Address, id=address_id, user=request.user)
            edit_address_form = AddressForm(request.POST, instance=edit_address)
            if edit_address_form.is_valid():
                updated_address = edit_address_form.save()
                if updated_address.is_default:
                    Address.objects.filter(user=request.user).exclude(id=updated_address.id).update(is_default=False)
                elif not Address.objects.filter(user=request.user, is_default=True).exists():
                    updated_address.is_default = True
                    updated_address.save(update_fields=['is_default'])

                messages.success(request, 'Address updated successfully.')
                return redirect('user_profile')
            messages.error(request, 'Please fix address edit form errors.')

    context = {
        'profile_user': request.user,
        'profile_form': profile_form,
        'address_form': address_form,
        'addresses': addresses,
        'edit_address': edit_address,
        'edit_address_form': edit_address_form,
        'recent_orders': Order.objects.filter(user=request.user).order_by('-created_at')[:3],
    }
    return render(request, 'main/profile.html', context)


@login_required(login_url='login')
def delete_address(request, address_id):
    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        was_default = address.is_default
        address.delete()

        if was_default:
            next_default = Address.objects.filter(user=request.user).first()
            if next_default:
                next_default.is_default = True
                next_default.save(update_fields=['is_default'])

        messages.success(request, 'Address deleted successfully.')
    return redirect('user_profile')


@login_required(login_url='login')
def set_default_address(request, address_id):
    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        Address.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save(update_fields=['is_default'])
        messages.success(request, 'Default address updated.')
    return redirect('user_profile')




# Simple FAQ search API used by the front-end chatbot widget
from django.http import JsonResponse
from django.db import DatabaseError


def faq_search(request):
    q = request.GET.get('q', '').strip()
    results = []
    try:
        faqs = FAQ.objects.all().order_by('-created')
        for f in faqs:
            if f.matches(q):
                results.append({
                    'id': f.id,
                    'question': f.question,
                    'answer': f.answer,
                    'keywords': f.keywords,
                })
        return JsonResponse({'results': results})
    except DatabaseError:
        # If DB table does not exist yet or DB is unavailable, return an empty list
        return JsonResponse({'results': []})


def faq_reply(request):
    """Return a single best answer for a user's question (GET param 'q').
    If no good match is found, return suggestions and a friendly fallback message.
    """
    q = request.GET.get('q', '').strip()
    try:
        faqs = list(FAQ.objects.all().order_by('-created'))
    except DatabaseError:
        return JsonResponse({'found': False, 'message': 'Service temporarily unavailable. Please try again later.', 'suggestions': []}, status=503)

    # Try to find a clear match
    matches = [f for f in faqs if f.matches(q)] if q else []

    # Basic scoring: prefer exact substring in question, then answer, then keywords
    def score(f):
        s = 0
        lq = q.lower()
        if lq in f.question.lower():
            s += 30
        if lq in f.answer.lower():
            s += 20
        for k in f.keywords_list():
            if lq == k:
                s += 20
            elif lq in k or k in lq:
                s += 10
        return s

    best = None
    if matches:
        scored = sorted(matches, key=score, reverse=True)
        best = scored[0]
    else:
        # try looser scoring across all faqs
        scored_all = sorted(faqs, key=score, reverse=True)
        if scored_all and score(scored_all[0]) > 0:
            best = scored_all[0]

    if best:
        return JsonResponse({'found': True, 'question': best.question, 'answer': best.answer})

    # fallback: return top 3 suggestions
    suggestions = [{ 'id': f.id, 'question': f.question, 'keywords': f.keywords } for f in faqs[:3]]
    return JsonResponse({'found': False, 'message': "Sorry, I couldn't find an exact answer. Here are some suggestions:", 'suggestions': suggestions})




