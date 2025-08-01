"""
Servicios para la generación de reportes
"""
import os
import csv
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.db.models import Count, Sum, Avg, Q
from .models import Report
from apps.residents.models import Resident
from apps.staff.models import Staff
from apps.facilities.models import Room
from apps.financial.models import Expense, Income, Investment, Category, CashFlow, Budget


class ReportGenerator:
    """Clase para generar diferentes tipos de reportes"""
    
    def __init__(self, report):
        self.report = report
        self.reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate(self):
        """Genera el reporte según su tipo"""
        try:
            self.report.status = 'processing'
            self.report.save()
            
            if self.report.report_type == 'residents':
                return self._generate_residents_report()
            elif self.report.report_type == 'staff':
                return self._generate_staff_report()
            elif self.report.report_type == 'facilities':
                return self._generate_facilities_report()
            elif self.report.report_type == 'financial':
                return self._generate_financial_report()
            elif self.report.report_type == 'medical':
                return self._generate_medical_report()
            elif self.report.report_type == 'occupancy':
                return self._generate_occupancy_report()
            else:
                return self._generate_custom_report()
                
        except Exception as e:
            self.report.status = 'failed'
            self.report.save()
            raise e
    
    def _generate_residents_report(self):
        """Genera reporte de residentes"""
        residents = Resident.objects.all()
        
        # Determinar si es un reporte rápido o específico basado en el título
        is_quick_report = 'Week' in self.report.title or 'Month' in self.report.title or 'Today' in self.report.title
        
        # Aplicar filtros de fecha solo para reportes específicos, no para reportes rápidos
        if not is_quick_report and self.report.date_from and self.report.date_to:
            residents = residents.filter(admission_date__gte=self.report.date_from, 
                                      admission_date__lte=self.report.date_to)
        
        # Aplicar filtros adicionales desde JSON
        filters = self.report.filters or {}
        if filters.get('status'):
            if filters['status'] == 'active':
                residents = residents.filter(is_in_treatment=True)
            elif filters['status'] == 'inactive':
                residents = residents.filter(is_in_treatment=False)
        
        if filters.get('gender'):
            residents = residents.filter(gender=filters['gender'])
        
        if filters.get('room_status'):
            if filters['room_status'] == 'assigned':
                residents = residents.filter(room__isnull=False)
            elif filters['room_status'] == 'unassigned':
                residents = residents.filter(room__isnull=True)
        
        # Filtros de edad
        if filters.get('min_age'):
            min_age_date = timezone.now().date() - timedelta(days=filters['min_age'] * 365)
            residents = residents.filter(date_of_birth__lte=min_age_date)
        
        if filters.get('max_age'):
            max_age_date = timezone.now().date() - timedelta(days=filters['max_age'] * 365)
            residents = residents.filter(date_of_birth__gte=max_age_date)
        
        # Generar archivo CSV
        return self._generate_csv_residents(residents)
    
    def _generate_staff_report(self):
        """Genera reporte de personal"""
        staff = Staff.objects.all()
        
        # Determinar si es un reporte rápido o específico basado en el título
        is_quick_report = 'Week' in self.report.title or 'Month' in self.report.title or 'Today' in self.report.title
        
        # Aplicar filtros de fecha solo para reportes específicos, no para reportes rápidos
        if not is_quick_report and self.report.date_from and self.report.date_to:
            staff = staff.filter(hire_date__gte=self.report.date_from, 
                               hire_date__lte=self.report.date_to)
        
        # Aplicar filtros adicionales
        filters = self.report.filters or {}
        if filters.get('status'):
            staff = staff.filter(employment_status=filters['status'])
        
        if filters.get('department'):
            staff = staff.filter(department=filters['department'])
        
        if filters.get('min_salary'):
            staff = staff.filter(salary__gte=filters['min_salary'])
        
        if filters.get('max_salary'):
            staff = staff.filter(salary__lte=filters['max_salary'])
        
        # Generar archivo CSV
        return self._generate_csv_staff(staff)
    
    def _generate_facilities_report(self):
        """Genera reporte de instalaciones"""
        rooms = Room.objects.all()
        
        # Aplicar filtros
        filters = self.report.filters or {}
        if filters.get('status'):
            rooms = rooms.filter(status=filters['status'])
        
        if filters.get('floor'):
            rooms = rooms.filter(floor=filters['floor'])
        
        # Generar archivo CSV
        return self._generate_csv_facilities(rooms)
    
    def _generate_financial_report(self):
        """Genera reporte financiero con datos reales"""
        # Obtener datos financieros
        expenses = Expense.objects.all()
        incomes = Income.objects.all()
        investments = Investment.objects.all()
        categories = Category.objects.all()
        
        # Aplicar filtros de fecha si están especificados
        if self.report.date_from and self.report.date_to:
            expenses = expenses.filter(expense_date__gte=self.report.date_from, 
                                    expense_date__lte=self.report.date_to)
            incomes = incomes.filter(income_date__gte=self.report.date_from, 
                                   income_date__lte=self.report.date_to)
            investments = investments.filter(planned_date__gte=self.report.date_from, 
                                          planned_date__lte=self.report.date_to)
        
        # Aplicar filtros adicionales
        filters = self.report.filters or {}
        if filters.get('expense_status'):
            expenses = expenses.filter(status=filters['expense_status'])
        
        if filters.get('income_status'):
            incomes = incomes.filter(status=filters['income_status'])
        
        if filters.get('investment_status'):
            investments = investments.filter(status=filters['investment_status'])
        
        if filters.get('category_type'):
            categories = categories.filter(category_type=filters['category_type'])
        
        # Calcular estadísticas
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        total_incomes = incomes.aggregate(total=Sum('amount'))['total'] or 0
        total_investments = investments.aggregate(total=Sum('amount'))['total'] or 0
        net_income = total_incomes - total_expenses
        
        financial_data = {
            'expenses': expenses,
            'incomes': incomes,
            'investments': investments,
            'categories': categories,
            'statistics': {
                'total_expenses': total_expenses,
                'total_incomes': total_incomes,
                'total_investments': total_investments,
                'net_income': net_income,
                'expense_count': expenses.count(),
                'income_count': incomes.count(),
                'investment_count': investments.count(),
            }
        }
        
        # Generar archivo CSV
        return self._generate_csv_financial(financial_data)
    
    def _generate_medical_report(self):
        """Genera reporte médico (placeholder - implementar cuando haya módulo médico)"""
        # Por ahora, generar un reporte básico de residentes con información médica
        residents = Resident.objects.all()
        
        # Aplicar filtros de fecha si están especificados
        if self.report.date_from and self.report.date_to:
            residents = residents.filter(admission_date__gte=self.report.date_from, 
                                      admission_date__lte=self.report.date_to)
        
        return self._generate_csv_medical(residents)
    
    def _generate_occupancy_report(self):
        """Genera reporte de ocupación"""
        rooms = Room.objects.all()
        
        # Calcular estadísticas de ocupación
        total_rooms = rooms.count()
        available_rooms = rooms.filter(status='available').count()
        maintenance_rooms = rooms.filter(status='maintenance').count()
        quarantine_rooms = rooms.filter(status='quarantine').count()
        
        # Calcular habitaciones ocupadas basándose en camas ocupadas
        total_beds = sum(room.total_beds for room in rooms)
        occupied_beds = sum(room.occupied_beds for room in rooms)
        occupied_rooms = sum(1 for room in rooms if room.occupied_beds > 0)
        
        occupancy_data = {
            'total_rooms': total_rooms,
            'total_beds': total_beds,
            'occupied_rooms': occupied_rooms,
            'occupied_beds': occupied_beds,
            'available_rooms': available_rooms,
            'maintenance_rooms': maintenance_rooms,
            'quarantine_rooms': quarantine_rooms,
            'occupancy_rate': round((occupied_beds / total_beds * 100), 2) if total_beds > 0 else 0,
            'rooms': rooms
        }
        
        # Generar archivo CSV
        return self._generate_csv_occupancy(occupancy_data)
    
    def _generate_custom_report(self):
        """Genera reporte personalizado"""
        # Por ahora, generar un reporte combinado de residentes y personal
        residents = Resident.objects.all()
        staff = Staff.objects.all()
        
        # Aplicar filtros de fecha si están especificados
        if self.report.date_from and self.report.date_to:
            residents = residents.filter(admission_date__gte=self.report.date_from, 
                                      admission_date__lte=self.report.date_to)
            staff = staff.filter(hire_date__gte=self.report.date_from, 
                               hire_date__lte=self.report.date_to)
        
        custom_data = {
            'residents': residents,
            'staff': staff,
            'total_residents': residents.count(),
            'total_staff': staff.count(),
        }
        
        return self._generate_csv_custom(custom_data)
    
    def _generate_csv_residents(self, residents):
        """Genera CSV de residentes"""
        filename = f"residents_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Nombre', 'Apellidos', 'Fecha de Nacimiento', 'Edad', 'Género', 
                         'Fecha de Admisión', 'Habitación', 'Teléfono', 'Email', 'Estado de Tratamiento']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for resident in residents:
                writer.writerow({
                    'ID': resident.id,
                    'Nombre': resident.first_name,
                    'Apellidos': resident.last_name,
                    'Fecha de Nacimiento': resident.date_of_birth,
                    'Edad': resident.age,
                    'Género': resident.get_gender_display(),
                    'Fecha de Admisión': resident.admission_date,
                    'Habitación': resident.room.room_number if resident.room else 'Sin asignar',
                    'Teléfono': resident.phone,
                    'Email': resident.email,
                    'Estado de Tratamiento': 'En Tratamiento' if resident.is_in_treatment else 'No en Tratamiento'
                })
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_staff(self, staff):
        """Genera CSV de personal"""
        filename = f"staff_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Nombre', 'Apellidos', 'Departamento', 'Cargo', 'Estado', 
                         'Fecha de Contratación', 'Salario', 'Teléfono', 'Email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for employee in staff:
                writer.writerow({
                    'ID': employee.id,
                    'Nombre': employee.first_name,
                    'Apellidos': employee.last_name,
                    'Departamento': employee.get_department_display(),
                    'Cargo': employee.position,
                    'Estado': employee.get_employment_status_display(),
                    'Fecha de Contratación': employee.hire_date,
                    'Salario': employee.salary,
                    'Teléfono': employee.phone,
                    'Email': employee.email
                })
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_facilities(self, rooms):
        """Genera CSV de instalaciones"""
        filename = f"facilities_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Número de Habitación', 'Piso', 'Tipo', 'Estado', 
                         'Total de Camas', 'Camas Ocupadas', 'Camas Disponibles']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for room in rooms:
                available_beds = room.total_beds - room.occupied_beds
                writer.writerow({
                    'ID': room.id,
                    'Número de Habitación': room.room_number,
                    'Piso': room.floor,
                    'Tipo': room.get_room_type_display(),
                    'Estado': room.get_status_display(),
                    'Total de Camas': room.total_beds,
                    'Camas Ocupadas': room.occupied_beds,
                    'Camas Disponibles': available_beds
                })
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_financial(self, financial_data):
        """Genera CSV de reporte financiero"""
        filename = f"financial_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Primera hoja: Resumen
            writer = csv.writer(csvfile)
            writer.writerow(['REPORTE FINANCIERO'])
            writer.writerow([f'Generado el: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'])
            writer.writerow([])
            
            # Estadísticas generales
            stats = financial_data['statistics']
            writer.writerow(['ESTADÍSTICAS GENERALES'])
            writer.writerow(['Total Gastos', f'${stats["total_expenses"]:,.2f}'])
            writer.writerow(['Total Ingresos', f'${stats["total_incomes"]:,.2f}'])
            writer.writerow(['Total Inversiones', f'${stats["total_investments"]:,.2f}'])
            writer.writerow(['Ingreso Neto', f'${stats["net_income"]:,.2f}'])
            writer.writerow(['Cantidad de Gastos', stats['expense_count']])
            writer.writerow(['Cantidad de Ingresos', stats['income_count']])
            writer.writerow(['Cantidad de Inversiones', stats['investment_count']])
            writer.writerow([])
            
            # Gastos
            writer.writerow(['DETALLE DE GASTOS'])
            writer.writerow(['ID', 'Título', 'Categoría', 'Monto', 'Fecha', 'Estado', 'Proveedor'])
            for expense in financial_data['expenses']:
                writer.writerow([
                    expense.id,
                    expense.title,
                    expense.category.name,
                    f'${expense.amount:,.2f}',
                    expense.expense_date,
                    expense.get_status_display(),
                    expense.supplier
                ])
            writer.writerow([])
            
            # Ingresos
            writer.writerow(['DETALLE DE INGRESOS'])
            writer.writerow(['ID', 'Título', 'Categoría', 'Monto', 'Fecha', 'Estado', 'Cliente'])
            for income in financial_data['incomes']:
                writer.writerow([
                    income.id,
                    income.title,
                    income.category.name,
                    f'${income.amount:,.2f}',
                    income.income_date,
                    income.get_status_display(),
                    income.client
                ])
            writer.writerow([])
            
            # Inversiones
            writer.writerow(['DETALLE DE INVERSIONES'])
            writer.writerow(['ID', 'Título', 'Tipo', 'Monto', 'Fecha Planificada', 'Estado', 'Progreso (%)'])
            for investment in financial_data['investments']:
                writer.writerow([
                    investment.id,
                    investment.title,
                    investment.get_investment_type_display(),
                    f'${investment.amount:,.2f}',
                    investment.planned_date,
                    investment.get_status_display(),
                    f'{investment.progress_percentage}%'
                ])
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_medical(self, residents):
        """Genera CSV de reporte médico"""
        filename = f"medical_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Nombre', 'Apellidos', 'Edad', 'Género', 'Fecha de Admisión', 
                         'Estado de Tratamiento', 'Notas de Tratamiento', 'Fecha de Fin de Tratamiento']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for resident in residents:
                writer.writerow({
                    'ID': resident.id,
                    'Nombre': resident.first_name,
                    'Apellidos': resident.last_name,
                    'Edad': resident.age,
                    'Género': resident.get_gender_display(),
                    'Fecha de Admisión': resident.admission_date,
                    'Estado de Tratamiento': 'En Tratamiento' if resident.is_in_treatment else 'No en Tratamiento',
                    'Notas de Tratamiento': resident.treatment_notes or 'Sin notas',
                    'Fecha de Fin de Tratamiento': resident.treatment_end_date or 'No especificada'
                })
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_occupancy(self, occupancy_data):
        """Genera CSV de ocupación"""
        filename = f"occupancy_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Primera sección: Resumen
            writer = csv.writer(csvfile)
            writer.writerow(['REPORTE DE OCUPACIÓN'])
            writer.writerow([f'Generado el: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'])
            writer.writerow([])
            
            # Estadísticas generales
            writer.writerow(['ESTADÍSTICAS GENERALES'])
            writer.writerow(['Total de Habitaciones', occupancy_data['total_rooms']])
            writer.writerow(['Total de Camas', occupancy_data['total_beds']])
            writer.writerow(['Habitaciones Ocupadas', occupancy_data['occupied_rooms']])
            writer.writerow(['Camas Ocupadas', occupancy_data['occupied_beds']])
            writer.writerow(['Habitaciones Disponibles', occupancy_data['available_rooms']])
            writer.writerow(['Habitaciones en Mantenimiento', occupancy_data['maintenance_rooms']])
            writer.writerow(['Habitaciones en Cuarentena', occupancy_data['quarantine_rooms']])
            writer.writerow(['Tasa de Ocupación (%)', f"{occupancy_data['occupancy_rate']}%"])
            writer.writerow([])
            
            # Detalle por habitación
            writer.writerow(['DETALLE POR HABITACIÓN'])
            writer.writerow(['Número', 'Piso', 'Tipo', 'Estado', 'Total Camas', 'Camas Ocupadas', 'Camas Disponibles'])
            for room in occupancy_data['rooms']:
                available_beds = room.total_beds - room.occupied_beds
                writer.writerow([
                    room.room_number,
                    room.floor,
                    room.get_room_type_display(),
                    room.get_status_display(),
                    room.total_beds,
                    room.occupied_beds,
                    available_beds
                ])
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_custom(self, custom_data):
        """Genera CSV de reporte personalizado"""
        filename = f"custom_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['REPORTE PERSONALIZADO'])
            writer.writerow([f'Generado el: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'])
            writer.writerow([])
            
            # Resumen
            writer.writerow(['RESUMEN'])
            writer.writerow(['Total de Residentes', custom_data['total_residents']])
            writer.writerow(['Total de Personal', custom_data['total_staff']])
            writer.writerow([])
            
            # Residentes
            writer.writerow(['RESIDENTES'])
            writer.writerow(['ID', 'Nombre', 'Apellidos', 'Edad', 'Género', 'Estado de Tratamiento'])
            for resident in custom_data['residents']:
                writer.writerow([
                    resident.id,
                    resident.first_name,
                    resident.last_name,
                    resident.age,
                    resident.get_gender_display(),
                    'En Tratamiento' if resident.is_in_treatment else 'No en Tratamiento'
                ])
            writer.writerow([])
            
            # Personal
            writer.writerow(['PERSONAL'])
            writer.writerow(['ID', 'Nombre', 'Apellidos', 'Departamento', 'Cargo', 'Estado'])
            for employee in custom_data['staff']:
                writer.writerow([
                    employee.id,
                    employee.first_name,
                    employee.last_name,
                    employee.get_department_display(),
                    employee.position,
                    employee.get_employment_status_display()
                ])
        
        return self._save_report_file(filepath, filename)
    
    def _save_report_file(self, filepath, filename):
        """Guarda la información del archivo generado"""
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            self.report.file_path = filepath
            self.report.file_size = file_size
            self.report.generated_at = timezone.now()
            self.report.status = 'completed'
            self.report.save()
            return True
        return False


def generate_report(report_id):
    """Función para generar un reporte en segundo plano"""
    try:
        report = Report.objects.get(id=report_id)
        generator = ReportGenerator(report)
        return generator.generate()
    except Report.DoesNotExist:
        return False


def download_report_file(report_id):
    """Función para descargar un archivo de reporte"""
    try:
        report = Report.objects.get(id=report_id)
        if report.is_completed and report.file_path and os.path.exists(report.file_path):
            with open(report.file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(report.file_path)}"'
                return response
    except Report.DoesNotExist:
        pass
    return None 