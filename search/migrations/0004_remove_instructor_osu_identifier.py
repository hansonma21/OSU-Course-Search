# Generated by Django 4.2.1 on 2023-05-06 05:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_alter_course_section_section_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instructor',
            name='osu_identifier',
        ),
    ]