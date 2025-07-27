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
from django.db.models import Count
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .models import Report
from apps.residents.models import Resident
from apps.staff.models import Staff
from apps.facilities.models import Room


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
        
        # Aplicar filtros
        if self.report.date_from:
            residents = residents.filter(admission_date__gte=self.report.date_from)
        if self.report.date_to:
            residents = residents.filter(admission_date__lte=self.report.date_to)
        
        # Aplicar filtros adicionales desde JSON
        filters = self.report.filters or {}
        if filters.get('status'):
            if filters['status'] == 'active':
                residents = residents.filter(is_active=True)
            elif filters['status'] == 'inactive':
                residents = residents.filter(is_active=False)
        
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
            residents = residents.filter(birth_date__lte=min_age_date)
        
        if filters.get('max_age'):
            max_age_date = timezone.now().date() - timedelta(days=filters['max_age'] * 365)
            residents = residents.filter(birth_date__gte=max_age_date)
        
        # Generar archivo según formato
        if self.report.format == 'csv':
            return self._generate_csv_residents(residents)
        elif self.report.format == 'json':
            return self._generate_json_residents(residents)
        else:
            return self._generate_pdf_residents(residents)
    
    def _generate_staff_report(self):
        """Genera reporte de personal"""
        staff = Staff.objects.all()
        
        # Aplicar filtros
        if self.report.date_from:
            staff = staff.filter(hire_date__gte=self.report.date_from)
        if self.report.date_to:
            staff = staff.filter(hire_date__lte=self.report.date_to)
        
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
        
        # Generar archivo según formato
        if self.report.format == 'csv':
            return self._generate_csv_staff(staff)
        elif self.report.format == 'json':
            return self._generate_json_staff(staff)
        else:
            return self._generate_pdf_staff(staff)
    
    def _generate_facilities_report(self):
        """Genera reporte de instalaciones"""
        rooms = Room.objects.all()
        
        # Aplicar filtros
        filters = self.report.filters or {}
        if filters.get('status'):
            rooms = rooms.filter(status=filters['status'])
        
        if filters.get('floor'):
            rooms = rooms.filter(floor=filters['floor'])
        
        # Generar archivo según formato
        if self.report.format == 'csv':
            return self._generate_csv_facilities(rooms)
        elif self.report.format == 'json':
            return self._generate_json_facilities(rooms)
        else:
            return self._generate_pdf_facilities(rooms)
    
    def _generate_financial_report(self):
        """Genera reporte financiero (placeholder)"""
        # Implementar lógica financiera cuando esté disponible
        return self._generate_placeholder_report('financial')
    
    def _generate_medical_report(self):
        """Genera reporte médico (placeholder)"""
        # Implementar lógica médica cuando esté disponible
        return self._generate_placeholder_report('medical')
    
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
            'occupancy_rate': round((occupied_beds / total_beds * 100), 2) if total_beds > 0 else 0
        }
        
        # Generar archivo según formato
        if self.report.format == 'csv':
            return self._generate_csv_occupancy(occupancy_data)
        elif self.report.format == 'json':
            return self._generate_json_occupancy(occupancy_data)
        else:
            return self._generate_pdf_occupancy(occupancy_data)
    
    def _generate_custom_report(self):
        """Genera reporte personalizado"""
        return self._generate_placeholder_report('custom')
    
    def _generate_csv_residents(self, residents):
        """Genera CSV de residentes"""
        filename = f"residents_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Nombre', 'Apellidos', 'Fecha de Nacimiento', 'Edad', 'Género', 
                         'Fecha de Admisión', 'Habitación', 'Estado', 'Teléfono', 'Email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for resident in residents:
                writer.writerow({
                    'ID': resident.id,
                    'Nombre': resident.first_name,
                    'Apellidos': resident.last_name,
                    'Fecha de Nacimiento': resident.birth_date,
                    'Edad': resident.age,
                    'Género': resident.get_gender_display(),
                    'Fecha de Admisión': resident.admission_date,
                    'Habitación': resident.room.number if resident.room else 'Sin asignar',
                    'Estado': 'Activo' if resident.is_active else 'Inactivo',
                    'Teléfono': resident.phone,
                    'Email': resident.email
                })
        
        return self._save_report_file(filepath, filename)
    
    def _generate_json_residents(self, residents):
        """Genera JSON de residentes"""
        filename = f"residents_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        data = {
            'report_info': {
                'title': self.report.title,
                'generated_at': timezone.now().isoformat(),
                'total_records': residents.count()
            },
            'residents': []
        }
        
        for resident in residents:
            data['residents'].append({
                'id': resident.id,
                'first_name': resident.first_name,
                'last_name': resident.last_name,
                'birth_date': resident.birth_date.isoformat() if resident.birth_date else None,
                'age': resident.age,
                'gender': resident.get_gender_display(),
                'admission_date': resident.admission_date.isoformat() if resident.admission_date else None,
                'room': resident.room.number if resident.room else None,
                'is_active': resident.is_active,
                'phone': resident.phone,
                'email': resident.email
            })
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_staff(self, staff):
        """Genera CSV de personal"""
        filename = f"staff_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Nombre', 'Apellidos', 'Departamento', 'Cargo', 'Fecha de Contratación',
                         'Salario', 'Estado', 'Teléfono', 'Email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for member in staff:
                writer.writerow({
                    'ID': member.id,
                    'Nombre': member.first_name,
                    'Apellidos': member.last_name,
                    'Departamento': member.get_department_display(),
                    'Cargo': member.position,
                    'Fecha de Contratación': member.hire_date,
                    'Salario': member.salary,
                    'Estado': member.get_employment_status_display(),
                    'Teléfono': member.phone,
                    'Email': member.email
                })
        
        return self._save_report_file(filepath, filename)
    
    def _generate_json_staff(self, staff):
        """Genera JSON de personal"""
        filename = f"staff_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        data = {
            'report_info': {
                'title': self.report.title,
                'generated_at': timezone.now().isoformat(),
                'total_records': staff.count()
            },
            'staff': []
        }
        
        for member in staff:
            data['staff'].append({
                'id': member.id,
                'first_name': member.first_name,
                'last_name': member.last_name,
                'department': member.get_department_display(),
                'position': member.position,
                'hire_date': member.hire_date.isoformat() if member.hire_date else None,
                'salary': float(member.salary) if member.salary else None,
                'employment_status': member.get_employment_status_display(),
                'phone': member.phone,
                'email': member.email
            })
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_facilities(self, rooms):
        """Genera CSV de instalaciones"""
        filename = f"facilities_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Número', 'Piso', 'Total Camas', 'Camas Ocupadas', 'Camas Disponibles', 'Estado', 'Descripción']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for room in rooms:
                writer.writerow({
                    'Número': room.room_number,
                    'Piso': room.floor,
                    'Total Camas': room.total_beds,
                    'Camas Ocupadas': room.occupied_beds,
                    'Camas Disponibles': room.available_beds,
                    'Estado': room.get_status_display(),
                    'Descripción': room.description or ''
                })
        
        return self._save_report_file(filepath, filename)
    
    def _generate_json_facilities(self, rooms):
        """Genera JSON de instalaciones"""
        filename = f"facilities_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        data = {
            'report_info': {
                'title': self.report.title,
                'generated_at': timezone.now().isoformat(),
                'total_records': rooms.count()
            },
            'rooms': []
        }
        
        for room in rooms:
            data['rooms'].append({
                'number': room.room_number,
                'floor': room.floor,
                'total_beds': room.total_beds,
                'occupied_beds': room.occupied_beds,
                'available_beds': room.available_beds,
                'status': room.get_status_display(),
                'description': room.description or ''
            })
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        return self._save_report_file(filepath, filename)
    
    def _generate_csv_occupancy(self, occupancy_data):
        """Genera CSV de ocupación"""
        filename = f"occupancy_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Métrica', 'Valor']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerow({'Métrica': 'Total de Habitaciones', 'Valor': occupancy_data['total_rooms']})
            writer.writerow({'Métrica': 'Total de Camas', 'Valor': occupancy_data['total_beds']})
            writer.writerow({'Métrica': 'Habitaciones Ocupadas', 'Valor': occupancy_data['occupied_rooms']})
            writer.writerow({'Métrica': 'Camas Ocupadas', 'Valor': occupancy_data['occupied_beds']})
            writer.writerow({'Métrica': 'Habitaciones Disponibles', 'Valor': occupancy_data['available_rooms']})
            writer.writerow({'Métrica': 'Habitaciones en Mantenimiento', 'Valor': occupancy_data['maintenance_rooms']})
            writer.writerow({'Métrica': 'Habitaciones en Cuarentena', 'Valor': occupancy_data['quarantine_rooms']})
            writer.writerow({'Métrica': 'Tasa de Ocupación (%)', 'Valor': occupancy_data['occupancy_rate']})
        
        return self._save_report_file(filepath, filename)
    
    def _generate_json_occupancy(self, occupancy_data):
        """Genera JSON de ocupación"""
        filename = f"occupancy_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        data = {
            'report_info': {
                'title': self.report.title,
                'generated_at': timezone.now().isoformat()
            },
            'occupancy_data': occupancy_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        return self._save_report_file(filepath, filename)
    
    def _generate_placeholder_report(self, report_type):
        """Genera un reporte placeholder para tipos no implementados"""
        filename = f"{report_type}_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as txtfile:
            txtfile.write(f"Reporte de {report_type.title()}\n")
            txtfile.write("=" * 50 + "\n")
            txtfile.write(f"Generado el: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            txtfile.write(f"Título: {self.report.title}\n")
            txtfile.write(f"Descripción: {self.report.description or 'Sin descripción'}\n")
            txtfile.write("\nEste tipo de reporte está en desarrollo.\n")
            txtfile.write("Próximamente estará disponible con datos completos.\n")
        
        return self._save_report_file(filepath, filename)
    
    def _generate_pdf_residents(self, residents):
        """Genera PDF de residentes"""
        filename = f"residents_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12
        )
        normal_style = styles['Normal']
        
        # Título del reporte
        story.append(Paragraph(self.report.title, title_style))
        story.append(Spacer(1, 12))
        
        # Información del reporte
        story.append(Paragraph(f"<b>Generado el:</b> {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        story.append(Paragraph(f"<b>Total de registros:</b> {residents.count()}", normal_style))
        story.append(Spacer(1, 20))
        
        # Tabla de residentes
        if residents.exists():
            # Definir encabezados según los filtros
            headers = ['ID', 'Nombre', 'Apellidos', 'Edad', 'Género', 'Habitación', 'Estado']
            col_widths = [0.5*inch, 1.2*inch, 1.2*inch, 0.6*inch, 0.8*inch, 1*inch, 0.8*inch]
            
            if filters.get('include_medical'):
                headers.append('Información Médica')
                col_widths.append(1.5*inch)
            
            if filters.get('include_emergency'):
                headers.append('Contacto Emergencia')
                col_widths.append(1.5*inch)
            
            data = [headers]
            
            for resident in residents:
                # Información básica
                row = [
                    str(resident.id),
                    resident.first_name or '',
                    resident.last_name or '',
                    str(resident.age) if resident.age else '',
                    resident.get_gender_display() if resident.gender else '',
                    resident.room.number if resident.room else 'Sin asignar',
                    'Activo' if resident.is_active else 'Inactivo'
                ]
                
                # Agregar información médica si se solicita
                if filters.get('include_medical'):
                    medical_info = []
                    if hasattr(resident, 'medical_conditions') and resident.medical_conditions:
                        medical_info.append(f"Condiciones: {resident.medical_conditions}")
                    if hasattr(resident, 'allergies') and resident.allergies:
                        medical_info.append(f"Alergias: {resident.allergies}")
                    if hasattr(resident, 'medications') and resident.medications:
                        medical_info.append(f"Medicamentos: {resident.medications}")
                    
                    row.append('; '.join(medical_info) if medical_info else 'Sin información médica')
                
                # Agregar información de emergencia si se solicita
                if filters.get('include_emergency'):
                    emergency_info = []
                    if hasattr(resident, 'emergency_contact_name') and resident.emergency_contact_name:
                        emergency_info.append(f"Contacto: {resident.emergency_contact_name}")
                    if hasattr(resident, 'emergency_contact_phone') and resident.emergency_contact_phone:
                        emergency_info.append(f"Tel: {resident.emergency_contact_phone}")
                    
                    row.append('; '.join(emergency_info) if emergency_info else 'Sin contacto de emergencia')
                
                data.append(row)
            
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Lista de Residentes", heading_style))
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Estadísticas
        if residents.exists():
            story.append(Paragraph("Estadísticas", heading_style))
            
            # Distribución por género
            gender_stats = residents.values('gender').annotate(count=Count('id'))
            gender_data = [['Género', 'Cantidad']]
            for stat in gender_stats:
                gender_data.append([stat['gender'] or 'No especificado', str(stat['count'])])
            
            gender_table = Table(gender_data, colWidths=[2*inch, 1*inch])
            gender_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(gender_table)
            story.append(Spacer(1, 12))
        
        doc.build(story)
        return self._save_report_file(filepath, filename)
    
    def _generate_pdf_staff(self, staff):
        """Genera PDF de personal"""
        filename = f"staff_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12
        )
        normal_style = styles['Normal']
        
        # Título del reporte
        story.append(Paragraph(self.report.title, title_style))
        story.append(Spacer(1, 12))
        
        # Información del reporte
        story.append(Paragraph(f"<b>Generado el:</b> {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        story.append(Paragraph(f"<b>Total de registros:</b> {staff.count()}", normal_style))
        story.append(Spacer(1, 20))
        
        # Tabla de personal
        if staff.exists():
            # Definir encabezados según los filtros
            headers = ['ID', 'Nombre', 'Apellidos', 'Departamento', 'Cargo', 'Estado']
            col_widths = [0.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch]
            
            if filters.get('include_salary'):
                headers.append('Información Salarial')
                col_widths.append(1.5*inch)
            
            if filters.get('include_schedule'):
                headers.append('Información Horarios')
                col_widths.append(1.5*inch)
            
            data = [headers]
            
            for member in staff:
                # Información básica
                row = [
                    str(member.id),
                    member.first_name or '',
                    member.last_name or '',
                    member.get_department_display() if member.department else '',
                    member.position or '',
                    member.get_employment_status_display() if member.employment_status else ''
                ]
                
                # Agregar información salarial si se solicita
                if filters.get('include_salary'):
                    salary_info = []
                    if hasattr(member, 'salary') and member.salary:
                        salary_info.append(f"Salario: €{member.salary}")
                    if hasattr(member, 'years_of_service') and member.years_of_service:
                        salary_info.append(f"Años servicio: {member.years_of_service}")
                    
                    row.append('; '.join(salary_info) if salary_info else 'Sin información salarial')
                
                # Agregar información de horarios si se solicita
                if filters.get('include_schedule'):
                    schedule_info = []
                    if hasattr(member, 'work_schedule') and member.work_schedule:
                        schedule_info.append(f"Horario: {member.work_schedule}")
                    if hasattr(member, 'shift') and member.shift:
                        schedule_info.append(f"Turno: {member.shift}")
                    
                    row.append('; '.join(schedule_info) if schedule_info else 'Sin información de horarios')
                
                data.append(row)
            
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Lista de Personal", heading_style))
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Estadísticas
        if staff.exists():
            story.append(Paragraph("Estadísticas", heading_style))
            
            # Distribución por departamento
            dept_stats = staff.values('department').annotate(count=Count('id'))
            dept_data = [['Departamento', 'Cantidad']]
            for stat in dept_stats:
                dept_data.append([stat['department'] or 'No especificado', str(stat['count'])])
            
            dept_table = Table(dept_data, colWidths=[2*inch, 1*inch])
            dept_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(dept_table)
            story.append(Spacer(1, 12))
        
        doc.build(story)
        return self._save_report_file(filepath, filename)
    
    def _generate_pdf_facilities(self, rooms):
        """Genera PDF de instalaciones"""
        filename = f"facilities_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12
        )
        normal_style = styles['Normal']
        
        # Título del reporte
        story.append(Paragraph(self.report.title, title_style))
        story.append(Spacer(1, 12))
        
        # Información del reporte
        story.append(Paragraph(f"<b>Generado el:</b> {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        story.append(Paragraph(f"<b>Total de habitaciones:</b> {rooms.count()}", normal_style))
        story.append(Spacer(1, 20))
        
        # Tabla de habitaciones
        if rooms.exists():
            data = [['Número', 'Piso', 'Total Camas', 'Camas Ocupadas', 'Camas Disponibles', 'Estado']]
            
            for room in rooms:
                data.append([
                    room.room_number,
                    str(room.floor) if room.floor else '',
                    str(room.total_beds) if room.total_beds else '',
                    str(room.occupied_beds) if room.occupied_beds else '',
                    str(room.available_beds) if room.available_beds else '',
                    room.get_status_display() if room.status else ''
                ])
            
            table = Table(data, colWidths=[1*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Lista de Habitaciones", heading_style))
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Estadísticas
        if rooms.exists():
            story.append(Paragraph("Estadísticas", heading_style))
            
            # Distribución por estado
            status_stats = rooms.values('status').annotate(count=Count('id'))
            status_data = [['Estado', 'Cantidad']]
            for stat in status_stats:
                status_data.append([stat['status'] or 'No especificado', str(stat['count'])])
            
            status_table = Table(status_data, colWidths=[2*inch, 1*inch])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(status_table)
            story.append(Spacer(1, 12))
        
        doc.build(story)
        return self._save_report_file(filepath, filename)
    
    def _generate_pdf_occupancy(self, occupancy_data):
        """Genera PDF de ocupación"""
        filename = f"occupancy_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12
        )
        normal_style = styles['Normal']
        
        # Título del reporte
        story.append(Paragraph(self.report.title, title_style))
        story.append(Spacer(1, 12))
        
        # Información del reporte
        story.append(Paragraph(f"<b>Generado el:</b> {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 20))
        
        # Tabla de estadísticas de ocupación
        data = [
            ['Métrica', 'Valor'],
            ['Total de Habitaciones', str(occupancy_data['total_rooms'])],
            ['Total de Camas', str(occupancy_data['total_beds'])],
            ['Habitaciones Ocupadas', str(occupancy_data['occupied_rooms'])],
            ['Camas Ocupadas', str(occupancy_data['occupied_beds'])],
            ['Habitaciones Disponibles', str(occupancy_data['available_rooms'])],
            ['Habitaciones en Mantenimiento', str(occupancy_data['maintenance_rooms'])],
            ['Habitaciones en Cuarentena', str(occupancy_data['quarantine_rooms'])],
            ['Tasa de Ocupación (%)', f"{occupancy_data['occupancy_rate']}%"]
        ]
        
        table = Table(data, colWidths=[3*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Estadísticas de Ocupación", heading_style))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Información adicional
        story.append(Paragraph("Información Adicional", heading_style))
        story.append(Paragraph(f"• La tasa de ocupación actual es del {occupancy_data['occupancy_rate']}%", normal_style))
        story.append(Paragraph(f"• Hay {occupancy_data['available_rooms']} habitaciones disponibles", normal_style))
        story.append(Paragraph(f"• {occupancy_data['maintenance_rooms']} habitaciones están en mantenimiento", normal_style))
        story.append(Paragraph(f"• {occupancy_data['quarantine_rooms']} habitaciones están en cuarentena", normal_style))
        
        doc.build(story)
        return self._save_report_file(filepath, filename)
    
    def _save_report_file(self, filepath, filename):
        """Guarda la información del archivo generado"""
        file_size = os.path.getsize(filepath)
        
        self.report.file_path = filepath
        self.report.file_size = file_size
        self.report.generated_at = timezone.now()
        self.report.status = 'completed'
        self.report.save()
        
        return filepath


def generate_report(report_id):
    """Función helper para generar un reporte"""
    try:
        report = Report.objects.get(id=report_id)
        generator = ReportGenerator(report)
        return generator.generate()
    except Report.DoesNotExist:
        raise ValueError(f"Reporte con ID {report_id} no encontrado")
    except Exception as e:
        raise e


def download_report_file(report_id):
    """Función helper para descargar un archivo de reporte"""
    try:
        report = Report.objects.get(id=report_id)
        
        if not report.file_path or not os.path.exists(report.file_path):
            raise FileNotFoundError("Archivo de reporte no encontrado")
        
        # Determinar el tipo MIME
        file_extension = os.path.splitext(report.file_path)[1].lower()
        mime_types = {
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain'
        }
        content_type = mime_types.get(file_extension, 'application/octet-stream')
        
        # Leer y devolver el archivo
        with open(report.file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(report.file_path)}"'
            return response
            
    except Report.DoesNotExist:
        raise ValueError(f"Reporte con ID {report_id} no encontrado")
    except Exception as e:
        raise e 