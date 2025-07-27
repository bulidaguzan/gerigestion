# Generated manually

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_number', models.CharField(help_text='Número único de la habitación', max_length=10, unique=True, verbose_name='Número de Habitación')),
                ('floor', models.PositiveIntegerField(help_text='Piso donde se encuentra la habitación', verbose_name='Piso')),
                ('total_beds', models.PositiveIntegerField(help_text='Número total de camas en la habitación', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Total de Camas')),
                ('occupied_beds', models.PositiveIntegerField(default=0, help_text='Número de camas actualmente ocupadas', verbose_name='Camas Ocupadas')),
                ('status', models.CharField(choices=[('available', 'Disponible'), ('maintenance', 'En Mantenimiento'), ('quarantine', 'En Cuarentena')], default='available', help_text='Estado actual de la habitación', max_length=20, verbose_name='Estado')),
                ('description', models.TextField(blank=True, help_text='Descripción adicional de la habitación', verbose_name='Descripción')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
            ],
            options={
                'verbose_name': 'Habitación',
                'verbose_name_plural': 'Habitaciones',
                'ordering': ['floor', 'room_number'],
            },
        ),
    ]
