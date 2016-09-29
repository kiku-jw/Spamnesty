# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-28 23:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import main.models


def add_domains(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Domain = apps.get_model("main", "Domain")
    Domain.objects.create(name="mnesty.com", company_name="MNesty, LLC")


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.CharField(default=main.models.generate_uuid, editable=False, max_length=30, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=1000)),
                ('company_name', models.CharField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(add_domains),
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['timestamp']},
        ),
        migrations.AlterField(
            model_name='message',
            name='message_id',
            field=models.CharField(max_length=1000, unique=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='domain',
            field=models.ForeignKey(default=main.models.get_random_domain, on_delete=django.db.models.deletion.CASCADE, to='main.Domain'),
        ),
    ]