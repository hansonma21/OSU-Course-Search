# Generated by Django 4.2.1 on 2024-08-12 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0010_course_section_created_date_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField()),
                ('date_posted', models.DateTimeField(auto_now_add=True)),
                ('display', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-date_posted'],
            },
        ),
    ]
