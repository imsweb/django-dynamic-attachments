# Generated by Django 3.2.13 on 2022-06-15 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0013_auto_20191107_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='file_size',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='upload',
            name='file_size',
            field=models.BigIntegerField(),
        ),
    ]
