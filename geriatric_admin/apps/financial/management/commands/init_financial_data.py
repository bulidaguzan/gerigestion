from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.financial.models import Category
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Command(BaseCommand):
    help = 'Inicializa datos básicos para la aplicación financiera'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando datos financieros...')
        
        # Obtener el primer superusuario o crear uno si no existe
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write('Creando superusuario...')
                user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS('Superusuario creado: admin/admin123'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear superusuario: {e}'))
            return

        # Categorías de Gastos
        expense_categories = [
            {
                'name': 'Alimentación',
                'description': 'Gastos en comida y bebidas para residentes y personal',
                'color': '#e74c3c'
            },
            {
                'name': 'Limpieza',
                'description': 'Productos de limpieza y servicios de aseo',
                'color': '#3498db'
            },
            {
                'name': 'Mantenimiento',
                'description': 'Reparaciones y mantenimiento de instalaciones',
                'color': '#f39c12'
            },
            {
                'name': 'Servicios Públicos',
                'description': 'Electricidad, agua, gas, internet, etc.',
                'color': '#9b59b6'
            },
            {
                'name': 'Personal',
                'description': 'Salarios, bonificaciones y gastos de personal',
                'color': '#1abc9c'
            },
            {
                'name': 'Medicamentos',
                'description': 'Medicamentos y suministros médicos',
                'color': '#e67e22'
            },
            {
                'name': 'Equipamiento',
                'description': 'Compra y mantenimiento de equipos',
                'color': '#34495e'
            },
            {
                'name': 'Marketing',
                'description': 'Publicidad y promoción del geriátrico',
                'color': '#e91e63'
            }
        ]

        # Categorías de Ingresos
        income_categories = [
            {
                'name': 'Pensiones de Residentes',
                'description': 'Pagos mensuales de los residentes',
                'color': '#27ae60'
            },
            {
                'name': 'Servicios Médicos',
                'description': 'Ingresos por servicios médicos adicionales',
                'color': '#2ecc71'
            },
            {
                'name': 'Actividades',
                'description': 'Ingresos por actividades y talleres',
                'color': '#16a085'
            },
            {
                'name': 'Donaciones',
                'description': 'Donaciones y contribuciones',
                'color': '#8e44ad'
            },
            {
                'name': 'Subvenciones',
                'description': 'Subvenciones gubernamentales',
                'color': '#2980b9'
            },
            {
                'name': 'Otros Servicios',
                'description': 'Otros servicios prestados',
                'color': '#f1c40f'
            }
        ]

        # Categorías de Inversiones
        investment_categories = [
            {
                'name': 'Infraestructura',
                'description': 'Mejoras en la infraestructura del geriátrico',
                'color': '#e67e22'
            },
            {
                'name': 'Tecnología',
                'description': 'Inversiones en tecnología y sistemas',
                'color': '#3498db'
            },
            {
                'name': 'Equipamiento Médico',
                'description': 'Compra de equipamiento médico',
                'color': '#e74c3c'
            },
            {
                'name': 'Capacitación',
                'description': 'Capacitación del personal',
                'color': '#9b59b6'
            },
            {
                'name': 'Marketing',
                'description': 'Inversiones en marketing y publicidad',
                'color': '#f39c12'
            }
        ]

        # Crear categorías de gastos
        for cat_data in expense_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                category_type='expense',
                defaults={
                    'description': cat_data['description'],
                    'color': cat_data['color'],
                    'created_by': user
                }
            )
            if created:
                self.stdout.write(f'Categoría de gasto creada: {category.name}')
            else:
                self.stdout.write(f'Categoría de gasto ya existe: {category.name}')

        # Crear categorías de ingresos
        for cat_data in income_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                category_type='income',
                defaults={
                    'description': cat_data['description'],
                    'color': cat_data['color'],
                    'created_by': user
                }
            )
            if created:
                self.stdout.write(f'Categoría de ingreso creada: {category.name}')
            else:
                self.stdout.write(f'Categoría de ingreso ya existe: {category.name}')

        # Crear categorías de inversiones
        for cat_data in investment_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                category_type='investment',
                defaults={
                    'description': cat_data['description'],
                    'color': cat_data['color'],
                    'created_by': user
                }
            )
            if created:
                self.stdout.write(f'Categoría de inversión creada: {category.name}')
            else:
                self.stdout.write(f'Categoría de inversión ya existe: {category.name}')

        self.stdout.write(self.style.SUCCESS('¡Datos financieros inicializados correctamente!'))
        self.stdout.write('Puedes acceder al sistema en: http://127.0.0.1:8000/financial/')
        self.stdout.write('Admin: http://127.0.0.1:8000/admin/') 