# Generated by Django 4.0.5 on 2022-06-20 10:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0022_partialtransactionallocation_capex_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partialtransactionallocation',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partial_allocations', to='finance.transaction'),
        ),
    ]
