# Generated by Django 4.0.5 on 2022-06-20 22:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0029_alter_transactionallocation_allocation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactioncapex',
            name='transaction',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='capex_allocation', to='finance.transaction'),
            preserve_default=False,
        ),
    ]
