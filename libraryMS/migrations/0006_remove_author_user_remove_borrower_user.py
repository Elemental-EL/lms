# Generated by Django 5.1.1 on 2024-09-16 15:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('libraryMS', '0005_author_user_borrower_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='author',
            name='user',
        ),
        migrations.RemoveField(
            model_name='borrower',
            name='user',
        ),
    ]
