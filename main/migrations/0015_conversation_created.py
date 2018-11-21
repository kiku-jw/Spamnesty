# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-26 13:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [("main", "0014_message_forwarder")]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="created",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        )
    ]