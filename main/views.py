from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from accounts.forms import RegistrationForm
from accounts.models import Address
import random

# Pages
def index(request):
    return render(request, 'main/index.html')

def menu_list(request):
    return render(request, 'main/menu_list.html')

def about(request):
    return render(request, 'main/about.html')

def contact(request):
    return render(request, 'main/contact.html')


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




# Simple FAQ search API used by the front-end chatbot widget
from django.http import JsonResponse
from .models import FAQ


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




