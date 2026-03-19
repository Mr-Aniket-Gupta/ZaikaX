from django.db import migrations, models


def create_initial_faqs(apps, schema_editor):
    FAQ = apps.get_model('main', 'FAQ')
    FAQs = [
        {
            'question': 'How do I place an order?',
            'answer': 'Browse the menu, add items to cart, and proceed to checkout. You can review your cart and provide delivery details before paying.',
            'keywords': 'order,place order,checkout,how to order',
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'We currently accept online UPI.',
            'keywords': 'payment,pay,card,upi,cod',
        },
        {
            'question': 'How long does delivery take?',
            'answer': 'Delivery times vary by location, usually between 30-60 minutes. ',
            'keywords': 'delivery,time,ETA,how long',
        },
        {
            'question': 'Can I cancel or change my order?',
            'answer': 'Order changes might be possible before it is prepared; please contact support ASAP. Cancellations may be subject to restaurant policy.',
            'keywords': 'cancel,change,modify,refund',
        },
    ]
    for i in FAQs:
        FAQ.objects.create(**i)


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=300)),
                ('answer', models.TextField()),
                ('keywords', models.CharField(blank=True, max_length=500, help_text='Comma-separated keywords')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RunPython(create_initial_faqs),
    ]
