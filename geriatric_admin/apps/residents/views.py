from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from datetime import date, timedelta
from .models import Resident, ResidentReport
from .forms import ResidentForm


@login_required
def resident_list(request):
    """Vista para listar todos los residentes"""
    # Parámetros de búsqueda y filtrado
    search = request.GET.get('search', '')
    gender_filter = request.GET.get('gender', '')
    marital_status_filter = request.GET.get('marital_status', '')
    
    # Query base
    residents = Resident.objects.all()
    
    # Aplicar filtros
    if search:
        residents = residents.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    
    if gender_filter:
        residents = residents.filter(gender=gender_filter)
    
    if marital_status_filter:
        residents = residents.filter(marital_status=marital_status_filter)
    
    # Paginación
    paginator = Paginator(residents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_residents = residents.count()
    male_residents = residents.filter(gender='M').count()
    female_residents = residents.filter(gender='F').count()
    other_residents = residents.filter(gender='O').count()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'gender_filter': gender_filter,
        'marital_status_filter': marital_status_filter,
        'total_residents': total_residents,
        'male_residents': male_residents,
        'female_residents': female_residents,
        'other_residents': other_residents,
        'gender_choices': Resident.GENDER_CHOICES,
        'marital_status_choices': Resident.MARITAL_STATUS_CHOICES,
    }
    
    return render(request, 'residents/list.html', context)


@login_required
def resident_detail(request, resident_id):
    """Vista para mostrar detalles de un residente"""
    resident = get_object_or_404(Resident, id=resident_id)
    
    # Obtener informes recientes del residente
    recent_reports = resident.reports.all()[:5]
    
    context = {
        'resident': resident,
        'recent_reports': recent_reports,
    }
    
    return render(request, 'residents/detail.html', context)


@login_required
def resident_create(request):
    """Vista para crear un nuevo residente"""
    if request.method == 'POST':
        form = ResidentForm(request.POST)
        if form.is_valid():
            resident = form.save()
            messages.success(request, _('Residente creado exitosamente.'))
            return redirect('residents_web:resident_detail', resident_id=resident.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = ResidentForm()
    
    context = {
        'form': form,
        'action': 'create',
    }
    
    return render(request, 'residents/form.html', context)


@login_required
def resident_update(request, resident_id):
    """Vista para actualizar un residente"""
    resident = get_object_or_404(Resident, id=resident_id)
    
    if request.method == 'POST':
        form = ResidentForm(request.POST, instance=resident)
        if form.is_valid():
            form.save()
            messages.success(request, _('Residente actualizado exitosamente.'))
            return redirect('residents_web:resident_detail', resident_id=resident.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = ResidentForm(instance=resident)
    
    context = {
        'form': form,
        'resident': resident,
        'action': 'update',
    }
    
    return render(request, 'residents/form.html', context)


@login_required
def resident_delete(request, resident_id):
    """Vista para eliminar un residente"""
    resident = get_object_or_404(Resident, id=resident_id)
    
    if request.method == 'POST':
        resident.delete()
        messages.success(request, _('Residente eliminado exitosamente.'))
        return redirect('residents_web:resident_list')
    
    context = {
        'resident': resident,
    }
    
    return render(request, 'residents/delete.html', context)


@login_required
def resident_dashboard(request):
    """Vista del dashboard de residentes con estadísticas"""
    # Estadísticas generales
    total_residents = Resident.objects.count()
    male_count = Resident.objects.filter(gender='M').count()
    female_count = Resident.objects.filter(gender='F').count()
    other_residents = Resident.objects.filter(gender='O').count()
    
    # Residentes activos (todos los residentes están activos por defecto)
    active_residents = total_residents
    
    # Estadísticas de tratamiento
    in_treatment = Resident.objects.filter(is_in_treatment=True).count()
    not_in_treatment = Resident.objects.filter(is_in_treatment=False).count()
    
    # Residentes recientes (últimos 30 días)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_admissions = Resident.objects.filter(admission_date__gte=thirty_days_ago).count()
    
    # Altas recientes (simulado como admisiones recientes)
    recent_discharges = recent_admissions
    
    # Promedio de edad
    if total_residents > 0:
        # Calcular edad para cada residente
        total_age = 0
        for resident in Resident.objects.all():
            total_age += resident.age
        avg_age = round(total_age / total_residents, 1)
    else:
        avg_age = 0
    
    # Tasa de ocupación (residentes con habitación asignada)
    residents_with_room = Resident.objects.filter(room__isnull=False).count()
    if total_residents > 0:
        occupancy_rate = round((residents_with_room / total_residents) * 100, 1)
    else:
        occupancy_rate = 0
    
    # Residentes recientes (últimos 5 residentes)
    recent_residents = Resident.objects.order_by('-admission_date')[:5]
    
    # Distribución por edad
    age_groups = {
        '60-70': Resident.objects.filter(date_of_birth__year__lte=date.today().year - 60, 
                                        date_of_birth__year__gte=date.today().year - 70).count(),
        '71-80': Resident.objects.filter(date_of_birth__year__lte=date.today().year - 71, 
                                        date_of_birth__year__gte=date.today().year - 80).count(),
        '81-90': Resident.objects.filter(date_of_birth__year__lte=date.today().year - 81, 
                                        date_of_birth__year__gte=date.today().year - 90).count(),
        '90+': Resident.objects.filter(date_of_birth__year__lte=date.today().year - 91).count(),
    }
    
    # Residentes sin habitación asignada
    unassigned_residents = Resident.objects.filter(room__isnull=True).count()
    
    # Informes pendientes
    pending_reports = ResidentReport.objects.filter(status='draft').count()
    
    # Estadísticas de salud (simuladas basadas en edad)
    # Residentes menores de 70 años
    excellent_health = Resident.objects.filter(
        date_of_birth__year__gt=date.today().year - 70
    ).count()
    
    # Residentes entre 70 y 79 años
    good_health = Resident.objects.filter(
        date_of_birth__year__lte=date.today().year - 70,
        date_of_birth__year__gt=date.today().year - 80
    ).count()
    
    # Residentes entre 80 y 89 años
    fair_health = Resident.objects.filter(
        date_of_birth__year__lte=date.today().year - 80,
        date_of_birth__year__gt=date.today().year - 90
    ).count()
    
    # Residentes de 90 años o más
    poor_health = Resident.objects.filter(
        date_of_birth__year__lte=date.today().year - 90
    ).count()
    
    context = {
        'total_residents': total_residents,
        'active_residents': active_residents,
        'in_treatment': in_treatment,
        'recent_discharges': recent_discharges,
        'avg_age': avg_age,
        'female_count': female_count,
        'male_count': male_count,
        'occupancy_rate': occupancy_rate,
        'recent_residents': recent_residents,
        'excellent_health': excellent_health,
        'good_health': good_health,
        'fair_health': fair_health,
        'poor_health': poor_health,
        'age_groups': age_groups,
        'unassigned_residents': unassigned_residents,
        'pending_reports': pending_reports,
    }
    
    return render(request, 'residents/dashboard.html', context)


@login_required
def resident_search(request):
    """Vista para búsqueda avanzada de residentes"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Resident.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(emergency_contact_name__icontains=query)
        )[:20]
    
    context = {
        'query': query,
        'results': results,
    }
    
    return render(request, 'residents/search.html', context)


# Vistas para informes periódicos
@login_required
def resident_reports_list(request, resident_id):
    """Vista para listar los informes de un residente"""
    resident = get_object_or_404(Resident, id=resident_id)
    reports = resident.reports.all().order_by('-report_date')
    
    # Paginación
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'resident': resident,
        'page_obj': page_obj,
    }
    
    return render(request, 'residents/reports/list.html', context)


@login_required
def resident_report_create(request, resident_id):
    """Vista para crear un nuevo informe de residente"""
    resident = get_object_or_404(Resident, id=resident_id)
    
    if request.method == 'POST':
        # Crear el informe con los datos del formulario
        report = ResidentReport(
            resident=resident,
            report_type=request.POST.get('report_type', 'monthly'),
            report_date=request.POST.get('report_date', date.today()),
            status=request.POST.get('status', 'draft'),
            physical_condition=request.POST.get('physical_condition', ''),
            mental_condition=request.POST.get('mental_condition', ''),
            social_activity=request.POST.get('social_activity', ''),
            medical_treatment=request.POST.get('medical_treatment', ''),
            medication_changes=request.POST.get('medication_changes', ''),
            incidents=request.POST.get('incidents', ''),
            goals_achieved=request.POST.get('goals_achieved', ''),
            next_goals=request.POST.get('next_goals', ''),
            recommendations=request.POST.get('recommendations', ''),
            created_by=request.user
        )
        report.save()
        
        messages.success(request, _('Informe creado exitosamente.'))
        return redirect('residents_web:resident_report_detail', resident_id=resident.id, report_id=report.id)
    
    context = {
        'resident': resident,
        'report_types': ResidentReport.REPORT_TYPES,
        'status_choices': ResidentReport.STATUS_CHOICES,
    }
    
    return render(request, 'residents/reports/form.html', context)


@login_required
def resident_report_detail(request, resident_id, report_id):
    """Vista para mostrar detalles de un informe"""
    resident = get_object_or_404(Resident, id=resident_id)
    report = get_object_or_404(ResidentReport, id=report_id, resident=resident)
    
    context = {
        'resident': resident,
        'report': report,
    }
    
    return render(request, 'residents/reports/detail.html', context)


@login_required
def resident_report_update(request, resident_id, report_id):
    """Vista para actualizar un informe"""
    resident = get_object_or_404(Resident, id=resident_id)
    report = get_object_or_404(ResidentReport, id=report_id, resident=resident)
    
    if request.method == 'POST':
        # Actualizar el informe con los datos del formulario
        report.report_type = request.POST.get('report_type', report.report_type)
        report.report_date = request.POST.get('report_date', report.report_date)
        report.status = request.POST.get('status', report.status)
        report.physical_condition = request.POST.get('physical_condition', report.physical_condition)
        report.mental_condition = request.POST.get('mental_condition', report.mental_condition)
        report.social_activity = request.POST.get('social_activity', report.social_activity)
        report.medical_treatment = request.POST.get('medical_treatment', report.medical_treatment)
        report.medication_changes = request.POST.get('medication_changes', report.medication_changes)
        report.incidents = request.POST.get('incidents', report.incidents)
        report.goals_achieved = request.POST.get('goals_achieved', report.goals_achieved)
        report.next_goals = request.POST.get('next_goals', report.next_goals)
        report.recommendations = request.POST.get('recommendations', report.recommendations)
        report.save()
        
        messages.success(request, _('Informe actualizado exitosamente.'))
        return redirect('residents_web:resident_report_detail', resident_id=resident.id, report_id=report.id)
    
    context = {
        'resident': resident,
        'report': report,
        'report_types': ResidentReport.REPORT_TYPES,
        'status_choices': ResidentReport.STATUS_CHOICES,
    }
    
    return render(request, 'residents/reports/form.html', context)


@login_required
def resident_report_delete(request, resident_id, report_id):
    """Vista para eliminar un informe"""
    resident = get_object_or_404(Resident, id=resident_id)
    report = get_object_or_404(ResidentReport, id=report_id, resident=resident)
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, _('Informe eliminado exitosamente.'))
        return redirect('residents_web:resident_reports_list', resident_id=resident.id)
    
    context = {
        'resident': resident,
        'report': report,
    }
    
    return render(request, 'residents/reports/delete.html', context) 