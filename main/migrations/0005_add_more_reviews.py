from django.db import migrations


def add_more_reviews(apps, schema_editor):
    Review = apps.get_model('main', 'Review')
    more = [
        {
            'name': 'Vikram P',
            'text': 'Consistently great portions and on-time delivery. The spice level is spot on!',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Vikram+P&background=FFD7A7&color=5B2C6F',
        },
        {
            'name': 'Neha R',
            'text': 'Loved the vegetarian options and clear labeling. The dal was comforting and fresh.',
            'rating': 4,
            'avatar_url': 'https://ui-avatars.com/api/?name=Neha+R&background=FCE7F3&color=9C254D',
        },
        {
            'name': 'Amit K',
            'text': 'Good value for money and friendly service. Packing was neat.',
            'rating': 4,
            'avatar_url': 'https://ui-avatars.com/api/?name=Amit+K&background=CCF3FF&color=063F6A',
        },
        {
            'name': 'Priya S',
            'text': 'Perfect balance of flavors. The biryani was aromatic and delicious.',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Priya+S&background=FFE7D9&color=7A3E3E',
        },
        {
            'name': 'Karan M',
            'text': 'Quick delivery and warm food. Loved the chutney accompaniment.',
            'rating': 5,
            'avatar_url': 'https://ui-avatars.com/api/?name=Karan+M&background=E6FFFA&color=0B6E4F',
        },
        {
            'name': 'Sophia L',
            'text': 'Great flavors and clean packaging. The dessert was a nice touch.',
            'rating': 4,
            'avatar_url': 'https://ui-avatars.com/api/?name=Sophia+L&background=F8E7FF&color=4A235A',
        },
    ]

    for r in more:
        Review.objects.get_or_create(name=r['name'], defaults={'text': r['text'], 'rating': r['rating'], 'avatar_url': r['avatar_url']})


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_create_reviews'),
    ]

    operations = [
        migrations.RunPython(add_more_reviews),
    ]