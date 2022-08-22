# Generated by Django 4.0.5 on 2022-06-20 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0025_rename_partialtransactionallocation_transactionallocation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transactionallocation',
            name='capex',
        ),
        migrations.AddField(
            model_name='transactioncapex',
            name='value',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=8),
            preserve_default=False,
        ),
    ]