from django.db import migrations


def add_user_reviews(apps, schema_editor):
    Review = apps.get_model('main', 'Review')
    extras = [
        {
            'name': 'Sofia M',
            'text': 'Loved the packaging and the spices were balanced. Will order again.',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Sofia+M&background=C4B5FD&color=312E81',
        },
        {
            'name': 'Rahul S',
            'text': 'Good food at reasonable prices. The paneer butter masala is my favorite.',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Rahul+S&background=A7F3D0&color=034D34',
        },
        {
            'name': 'Anjali K',
            'text': 'Amazing flavors and prompt delivery! The biryani felt homemade — highly recommended.',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Anjali+K&background=FFB4A2&color=333333',
        },
    ]

    for r in extras:
        Review.objects.create(**r)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_add_more_reviews'),
    ]

    operations = [
        migrations.RunPython(add_user_reviews),
    ]