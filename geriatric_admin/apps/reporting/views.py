from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.urls import reverse
from datetime import datetime, timedelta
import json
import threading

from .models import Report
from .forms import (
    ReportForm, QuickReportForm, ResidentReportForm, StaffReportForm
)
from .services import generate_report, download_report_file
from apps.residents.models import Resident
from apps.staff.models import Staff
from apps.facilities.models import Room


@login_required
def reporting_dashboard(request):
    """Dashboard principal de reportes"""
    
    # Estadísticas generales
    total_reports = Report.objects.count()
    completed_reports = Report.objects.filter(status='completed').count()
    pending_reports = Report.objects.filter(status='pending').count()
    failed_reports = Report.objects.filter(status='failed').count()
    
    # Reportes recientes
    recent_reports = Report.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:5]
    
    # Reportes por tipo
    reports_by_type = Report.objects.values('report_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Plantillas activas (simplificado)
    active_templates = []
    
    # Widgets del dashboard (simplificado)
    dashboard_widgets = []
    
    context = {
        'total_reports': total_reports,
        'completed_reports': completed_reports,
        'pending_reports': pending_reports,
        'failed_reports': failed_reports,
        'recent_reports': recent_reports,
        'reports_by_type': reports_by_type,
        'active_templates': active_templates,
        'dashboard_widgets': dashboard_widgets,
    }
    
    return render(request, 'reporting/dashboard.html', context)


@login_required
def report_list(request):
    """Lista de reportes generados"""
    
    # Filtros
    report_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Query base
    reports = Report.objects.filter(created_by=request.user)
    
    # Aplicar filtros
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    if status:
        reports = reports.filter(status=status)
    
    if date_from:
        reports = reports.filter(created_at__date__gte=date_from)
    
    if date_to:
        reports = reports.filter(created_at__date__lte=date_to)
    
    if search:
        reports = reports.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Ordenar
    reports = reports.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'report_types': Report.REPORT_TYPES,
        'status_choices': Report.STATUS_CHOICES,
        'filters': {
            'type': report_type,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'reporting/report_list.html', context)


@login_required
def report_create(request):
    """Crear un nuevo reporte"""
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()
            
            # Generar el reporte en segundo plano
            def generate_report_background():
                try:
                    generate_report(report.id)
                except Exception as e:
                    report.status = 'failed'
                    report.save()
            
            thread = threading.Thread(target=generate_report_background)
            thread.daemon = True
            thread.start()
            
            messages.success(request, _('Reporte creado exitosamente. Se está generando en segundo plano.'))
            return redirect('reporting_web:report_detail', report.id)
    else:
        form = ReportForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'reporting/report_form.html', context)


@login_required
def report_update(request, report_id):
    """Actualizar un reporte existente"""
    
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, _('Reporte actualizado exitosamente.'))
            return redirect('reporting_web:report_detail', report.id)
    else:
        form = ReportForm(instance=report)
    
    context = {
        'form': form,
        'report': report,
        'action': 'update'
    }
    
    return render(request, 'reporting/report_form.html', context)


@login_required
def report_detail(request, report_id):
    """Detalles de un reporte"""
    
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    context = {
        'report': report
    }
    
    return render(request, 'reporting/report_detail.html', context)


@login_required
def report_delete(request, report_id):
    """Eliminar un reporte"""
    
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, _('Reporte eliminado exitosamente.'))
        return redirect('reporting_web:report_list')
    
    context = {
        'report': report
    }
    
    return render(request, 'reporting/report_delete.html', context)


@login_required
def quick_report(request):
    """Generar reportes rápidos"""
    
    if request.method == 'POST':
        form = QuickReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            period = form.cleaned_data['period']
            format_type = form.cleaned_data['format']
            
            # Obtener rango de fechas
            date_from, date_to = form.get_date_range()
            
            # Crear reporte
            title = f"{form.get_report_type_display()} - {period.title()}"
            report = Report.objects.create(
                title=title,
                report_type=report_type.split('_')[0],
                format=format_type,
                date_from=date_from,
                date_to=date_to,
                status='pending',
                created_by=request.user
            )
            
            # Generar el reporte en segundo plano
            def generate_report_background():
                try:
                    generate_report(report.id)
                except Exception as e:
                    report.status = 'failed'
                    report.save()
            
            thread = threading.Thread(target=generate_report_background)
            thread.daemon = True
            thread.start()
            
            messages.success(request, _('Reporte creado exitosamente. Se está generando en segundo plano.'))
            return redirect('reporting_web:report_detail', report.id)
    else:
        form = QuickReportForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'reporting/quick_report.html', context)


@login_required
def resident_report(request):
    """Reporte específico de residentes"""
    
    if request.method == 'POST':
        form = ResidentReportForm(request.POST)
        if form.is_valid():
            # Crear reporte en la base de datos
            title = f"Reporte de Residentes - {timezone.now().strftime('%d/%m/%Y')}"
            
            # Preparar filtros para el reporte
            filters = {}
            if form.cleaned_data.get('status'):
                filters['status'] = form.cleaned_data['status']
            if form.cleaned_data.get('gender'):
                filters['gender'] = form.cleaned_data['gender']
            if form.cleaned_data.get('room_status'):
                filters['room_status'] = form.cleaned_data['room_status']
            if form.cleaned_data.get('min_age'):
                filters['min_age'] = form.cleaned_data['min_age']
            if form.cleaned_data.get('max_age'):
                filters['max_age'] = form.cleaned_data['max_age']
            if form.cleaned_data.get('include_medical_info'):
                filters['include_medical'] = form.cleaned_data['include_medical_info']
            if form.cleaned_data.get('include_emergency_contacts'):
                filters['include_emergency'] = form.cleaned_data['include_emergency_contacts']
            
            # Crear el reporte
            report = Report.objects.create(
                title=title,
                description=f"Reporte de residentes con filtros aplicados. Total: {Resident.objects.count()} residentes.",
                report_type='residents',
                format='pdf',  # Por defecto PDF para reportes específicos
                date_from=form.cleaned_data.get('date_from'),
                date_to=form.cleaned_data.get('date_to'),
                filters=filters,
                status='pending',
                created_by=request.user
            )
            
            # Generar el reporte en segundo plano
            def generate_report_background():
                try:
                    generate_report(report.id)
                except Exception as e:
                    report.status = 'failed'
                    report.save()
            
            thread = threading.Thread(target=generate_report_background)
            thread.daemon = True
            thread.start()
            
            messages.success(request, _('Reporte de residentes creado exitosamente. Se está generando en segundo plano.'))
            return redirect('reporting_web:report_detail', report.id)
    else:
        form = ResidentReportForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'reporting/resident_report.html', context)


@login_required
def staff_report(request):
    """Reporte específico de personal"""
    
    if request.method == 'POST':
        form = StaffReportForm(request.POST)
        if form.is_valid():
            # Crear reporte en la base de datos
            title = f"Reporte de Personal - {timezone.now().strftime('%d/%m/%Y')}"
            
            # Preparar filtros para el reporte
            filters = {}
            if form.cleaned_data.get('status'):
                filters['status'] = form.cleaned_data['status']
            if form.cleaned_data.get('department'):
                filters['department'] = form.cleaned_data['department']
            if form.cleaned_data.get('min_salary'):
                filters['min_salary'] = float(form.cleaned_data['min_salary'])
            if form.cleaned_data.get('max_salary'):
                filters['max_salary'] = float(form.cleaned_data['max_salary'])
            if form.cleaned_data.get('include_salary_info'):
                filters['include_salary'] = form.cleaned_data['include_salary_info']
            if form.cleaned_data.get('include_schedule_info'):
                filters['include_schedule'] = form.cleaned_data['include_schedule_info']
            
            # Crear el reporte
            report = Report.objects.create(
                title=title,
                description=f"Reporte de personal con filtros aplicados. Total: {Staff.objects.count()} empleados.",
                report_type='staff',
                format='pdf',  # Por defecto PDF para reportes específicos
                date_from=form.cleaned_data.get('date_from'),
                date_to=form.cleaned_data.get('date_to'),
                filters=filters,
                status='pending',
                created_by=request.user
            )
            
            # Generar el reporte en segundo plano
            def generate_report_background():
                try:
                    generate_report(report.id)
                except Exception as e:
                    report.status = 'failed'
                    report.save()
            
            thread = threading.Thread(target=generate_report_background)
            thread.daemon = True
            thread.start()
            
            messages.success(request, _('Reporte de personal creado exitosamente. Se está generando en segundo plano.'))
            return redirect('reporting_web:report_detail', report.id)
    else:
        form = StaffReportForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'reporting/staff_report.html', context)


# Vistas de plantillas eliminadas para simplificar el sistema


@login_required
def report_search(request):
    """Búsqueda AJAX de reportes"""
    
    search = request.GET.get('search', '')
    
    if search:
        reports = Report.objects.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search),
            created_by=request.user
        )[:10]
    else:
        reports = Report.objects.filter(created_by=request.user)[:10]
    
    data = []
    for report in reports:
        data.append({
            'id': report.id,
            'title': report.title,
            'type': report.get_report_type_display(),
            'status': report.get_status_display(),
            'created_at': report.created_at.strftime('%d/%m/%Y %H:%M'),
            'url': reverse('reporting_web:report_detail', args=[report.id])
        })
    
    return JsonResponse({'reports': data})


@login_required
def report_status_update(request, report_id):
    """Actualizar estado de reporte via AJAX"""
    
    if request.method == 'POST':
        report = get_object_or_404(Report, id=report_id, created_by=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(Report.STATUS_CHOICES):
            report.status = new_status
            if new_status == 'completed':
                report.generated_at = timezone.now()
            report.save()
            
            return JsonResponse({
                'success': True,
                'status': report.get_status_display()
            })
    
    return JsonResponse({'success': False})


# Vistas de widgets eliminadas para simplificar el sistema


@login_required
def report_download(request, report_id):
    """Descargar un reporte generado"""
    
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    if not report.is_completed:
        messages.error(request, _('El reporte no está completado aún.'))
        return redirect('reporting_web:report_detail', report.id)
    
    try:
        response = download_report_file(report.id)
        return response
    except Exception as e:
        messages.error(request, _('Error al descargar el reporte: ') + str(e))
        return redirect('reporting_web:report_detail', report.id)


@login_required
def report_regenerate(request, report_id):
    """Regenerar un reporte"""
    
    report = get_object_or_404(Report, id=report_id, created_by=request.user)
    
    if request.method == 'POST':
        # Regenerar el reporte en segundo plano
        def regenerate_report_background():
            try:
                generate_report(report.id)
            except Exception as e:
                report.status = 'failed'
                report.save()
        
        thread = threading.Thread(target=regenerate_report_background)
        thread.daemon = True
        thread.start()
        
        messages.success(request, _('Reporte en proceso de regeneración.'))
        return redirect('reporting_web:report_detail', report.id)
    
    context = {
        'report': report
    }
    
    return render(request, 'reporting/report_regenerate.html', context) 