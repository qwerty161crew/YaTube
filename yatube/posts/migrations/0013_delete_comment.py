# Generated by Django 2.2.16 on 2023-03-19 11:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_post_created'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Comment',
        ),
    ]
