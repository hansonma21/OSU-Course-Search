# Generated by Django 4.2.15 on 2024-08-13 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0011_news'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='updated_date',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='instructor',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='instructor',
            name='updated_date',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
