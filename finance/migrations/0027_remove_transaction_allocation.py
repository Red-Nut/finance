# Generated by Django 4.0.5 on 2022-06-20 21:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0026_remove_transactionallocation_capex_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='allocation',
        ),
    ]
