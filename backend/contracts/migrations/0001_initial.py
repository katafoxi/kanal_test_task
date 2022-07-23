# Generated by Django 4.0.6 on 2022-07-23 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contracts',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('contract', models.IntegerField()),
                ('price_usd', models.IntegerField()),
                ('price_rub', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('date', models.DateField(blank=True, null=True)),
            ],
            options={
                'db_table': 'contracts',
                'managed': False,
            },
        ),
    ]