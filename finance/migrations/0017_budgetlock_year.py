# Generated by Django 4.0.5 on 2022-06-12 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0016_budgetlock'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetlock',
            name='year',
            field=models.IntegerField(default=2022),
            preserve_default=False,
        ),
    ]
