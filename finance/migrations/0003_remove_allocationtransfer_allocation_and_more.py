# Generated by Django 4.0.5 on 2022-06-03 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_rename_allocationtracking_allocationtransfer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='allocationtransfer',
            name='allocation',
        ),
        migrations.RemoveField(
            model_name='allocationtransfer',
            name='type',
        ),
        migrations.AddField(
            model_name='allocationtransfer',
            name='from_allocation',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='transfers_from', to='finance.allocation'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='allocationtransfer',
            name='to_allocation',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='transfers_to', to='finance.allocation'),
            preserve_default=False,
        ),
    ]
