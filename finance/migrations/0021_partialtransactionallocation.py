# Generated by Django 4.0.5 on 2022-06-20 07:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0020_alter_capexapproval_status_alter_transaction_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartialTransactionAllocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=2, max_digits=8)),
                ('allocation', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='partial_transactions', to='finance.allocation')),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='partial_allocations', to='finance.transaction')),
            ],
        ),
    ]
