# Generated by Django 2.2.28 on 2023-03-08 17:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_post_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
    ]