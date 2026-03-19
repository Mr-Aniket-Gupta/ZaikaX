from django.db import migrations


def add_more_faqs(apps, schema_editor):
    FAQ = apps.get_model('main', 'FAQ')

    extras = [
        {
            'question': 'Do you offer vegetarian options?',
            'answer': (
                'Yes — we offer a wide range of vegetarian dishes clearly '
                'labeled on the menu.'
            ),
            'keywords': 'vegetarian,veg,vegan,plant based',
        },
        {
            'question': 'Do you offer contactless delivery?',
            'answer': (
                'Choose contactless delivery at checkout when available, '
                'and the driver will leave the order at your door.'
            ),
            'keywords': 'contactless,delivery,no contact',
        },
        {
            'question': 'Can I track my order?',
            'answer': (
                'After placing an order, you will receive an estimated delivery '
                'time and order updates via SMS. Live tracking is not available yet.'
            ),
            'keywords': 'track,tracking,order status',
        },
        {
            'question': 'What if my order is missing or incorrect?',
            'answer': (
                'If items are missing or incorrect, please contact support '
                'immediately and we will arrange a replacement or refund '
                'according to our policy.'
            ),
            'keywords': 'missing,incorrect,wrong items,refund,replacement',
        },
        {
            'question': 'Do you accept corporate or bulk orders?',
            'answer': (
                'Yes — we accept corporate and bulk orders. Please contact '
                'support or email corporate@zaikax.example to discuss requirements.'
            ),
            'keywords': 'corporate,bulk,event,catering',
        },
        {
            'question': 'Where is ZaikaX located?',
            'answer': 'Our kitchen and head office are located in New Delhi, India.',
            'keywords': 'location,address,delhi,office',
        },
        {
            'question': 'How can I contact ZaikaX for support?',
            'answer': (
                'You can email us at support@zaikax.com or call '
                '+91 98765 43210 for urgent order-related help.'
            ),
            'keywords': 'contact,support,help,email,phone',
        },
        {
            'question': 'How long does it take to get a response for queries?',
            'answer': (
                'For non-urgent queries submitted through the contact form, '
                'we usually respond within 1–2 business days.'
            ),
            'keywords': 'response,time,query,contact form',
        },
        {
            'question': 'What kind of food does ZaikaX offer?',
            'answer': (
                'ZaikaX serves authentic Indian food prepared using traditional '
                'recipes, fresh ingredients, and home-style cooking methods.'
            ),
            'keywords': 'food,indian,authentic,menu',
        },
        {
            'question': 'Do you use fresh ingredients?',
            'answer': (
                'Yes, we source fresh and local ingredients daily to ensure '
                'quality and great taste in every dish.'
            ),
            'keywords': 'fresh,ingredients,quality,food',
        },
        {
            'question': 'Is ZaikaX suitable for vegetarian customers?',
            'answer': (
                'Yes, we offer a wide variety of vegetarian dishes including '
                'paneer, dal, chole, rajma, and veg biryani.'
            ),
            'keywords': 'vegetarian,veg,paneer,dal',
        },
        {
            'question': 'Does ZaikaX provide fast delivery?',
            'answer': (
                'Yes, we focus on quick and reliable delivery so you can enjoy '
                'fresh food without long waiting times.'
            ),
            'keywords': 'fast delivery,speed,order',
        },
    ]

    for faq in extras:
        FAQ.objects.get_or_create(
            question=faq['question'],
            defaults={
                'answer': faq['answer'],
                'keywords': faq['keywords'],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_create_faq'),
    ]

    operations = [
        migrations.RunPython(add_more_faqs),
    ]
