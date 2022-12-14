# Generated by Django 4.0.5 on 2022-07-26 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0034_alter_transaction_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Credit'), (2, 'Debit'), (3, 'Transfer'), (4, 'Transfer Duplicate'), (5, 'Excess Funds Reallocated'), (6, 'Budget Allocation')]),
        ),
    ]
