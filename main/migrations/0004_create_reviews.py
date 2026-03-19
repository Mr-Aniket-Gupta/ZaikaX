from django.db import migrations, models


def create_reviews(apps, schema_editor):
    Review = apps.get_model('main', 'Review')
    samples = [
        {
            'name': 'Anjali K',
            'text': 'Amazing flavors and prompt delivery! The biryani felt homemade — highly recommended.',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Anjali+K&background=FFB4A2&color=333333',
        },
        {
            'name': 'Rahul S',
            'text': 'Good food at reasonable prices. The paneer butter masala is my favorite.',
            'rating': 4,
            'avatar_url': 'https://ui-avatars.com/api/?name=Rahul+S&background=A7F3D0&color=034D34',
        },
        {
            'name': 'Sofia M',
            'text': 'Loved the packaging and the spices were balanced. Will order again.',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Sofia+M&background=C4B5FD&color=312E81',
        },
    ]

    for s in samples:
        Review.objects.create(**s)


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('main', '0003_alter_faq_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('text', models.TextField()),
                ('rating', models.PositiveSmallIntegerField(default=5)),
                ('avatar_url', models.URLField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RunPython(create_reviews),
    ]