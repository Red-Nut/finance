# Generated by Django 4.0.5 on 2022-06-03 13:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AllocationTracking',
            new_name='AllocationTransfer',
        ),
    ]
