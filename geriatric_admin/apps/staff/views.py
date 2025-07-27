from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
from .models import Staff
from .forms import StaffForm


@login_required
def staff_dashboard(request):
    """Dashboard principal del personal"""
    # Estadísticas generales
    total_staff = Staff.objects.count()
    active_staff = Staff.objects.filter(employment_status='active').count()
    inactive_staff = Staff.objects.filter(employment_status='inactive').count()
    suspended_staff = Staff.objects.filter(employment_status='suspended').count()
    
    # Estadísticas por departamento
    department_stats = Staff.objects.values('department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Estadísticas por posición
    position_stats = Staff.objects.values('position').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Empleados recién contratados (últimos 30 días)
    recent_hires = Staff.objects.filter(
        hire_date__gte=date.today() - timedelta(days=30)
    ).order_by('-hire_date')[:5]
    
    # Empleados con más años de servicio
    senior_staff = Staff.objects.filter(
        employment_status='active'
    ).order_by('hire_date')[:5]
    
    # Salario promedio por departamento
    avg_salary_by_dept = Staff.objects.filter(
        employment_status='active'
    ).values('department').annotate(
        avg_salary=Avg('salary')
    ).order_by('-avg_salary')
    
    context = {
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': inactive_staff,
        'suspended_staff': suspended_staff,
        'department_stats': department_stats,
        'position_stats': position_stats,
        'recent_hires': recent_hires,
        'senior_staff': senior_staff,
        'avg_salary_by_dept': avg_salary_by_dept,
    }
    
    return render(request, 'staff/dashboard.html', context)


@login_required
def staff_list(request):
    """Lista de empleados con filtros y búsqueda"""
    # Parámetros de búsqueda y filtros
    search = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    position_filter = request.GET.get('position', '')
    status_filter = request.GET.get('status', '')
    
    # Consulta base
    staff_list = Staff.objects.all()
    
    # Aplicar filtros
    if search:
        staff_list = staff_list.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(employee_id__icontains=search) |
            Q(email__icontains=search) |
            Q(position__icontains=search) |
            Q(department__icontains=search)
        )
    
    if department_filter:
        staff_list = staff_list.filter(department=department_filter)
    
    if position_filter:
        staff_list = staff_list.filter(position=position_filter)
    
    if status_filter:
        staff_list = staff_list.filter(employment_status=status_filter)
    
    # Ordenar por apellido y nombre
    staff_list = staff_list.order_by('last_name', 'first_name')
    
    # Paginación
    paginator = Paginator(staff_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener opciones para filtros
    departments = Staff.objects.values_list('department', flat=True).distinct().order_by('department')
    positions = Staff.objects.values_list('position', flat=True).distinct().order_by('position')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'department_filter': department_filter,
        'position_filter': position_filter,
        'status_filter': status_filter,
        'departments': departments,
        'positions': positions,
        'status_choices': Staff.EMPLOYMENT_STATUS_CHOICES,
    }
    
    return render(request, 'staff/list.html', context)


@login_required
def staff_detail(request, staff_id):
    """Vista para mostrar detalles de un empleado"""
    staff = get_object_or_404(Staff, id=staff_id)
    
    context = {
        'staff': staff,
    }
    
    return render(request, 'staff/detail.html', context)


@login_required
def staff_create(request):
    """Vista para crear un nuevo empleado"""
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            staff = form.save()
            messages.success(request, _('Empleado creado exitosamente.'))
            return redirect('staff_web:staff_detail', staff_id=staff.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = StaffForm()
    
    context = {
        'form': form,
        'action': 'create',
    }
    
    return render(request, 'staff/form.html', context)


@login_required
def staff_update(request, staff_id):
    """Vista para actualizar un empleado existente"""
    staff = get_object_or_404(Staff, id=staff_id)
    
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, _('Empleado actualizado exitosamente.'))
            return redirect('staff_web:staff_detail', staff_id=staff.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = StaffForm(instance=staff)
    
    context = {
        'form': form,
        'staff': staff,
        'action': 'update',
    }
    
    return render(request, 'staff/form.html', context)


@login_required
def staff_delete(request, staff_id):
    """Vista para eliminar un empleado"""
    staff = get_object_or_404(Staff, id=staff_id)
    
    if request.method == 'POST':
        employee_name = staff.full_name
        staff.delete()
        messages.success(request, _('Empleado {} eliminado exitosamente.').format(employee_name))
        return redirect('staff_web:staff_list')
    
    context = {
        'staff': staff,
    }
    
    return render(request, 'staff/delete.html', context)


@login_required
def staff_search(request):
    """Vista AJAX para búsqueda de empleados"""
    search = request.GET.get('q', '')
    
    if len(search) < 2:
        return JsonResponse({'results': []})
    
    staff_list = Staff.objects.filter(
        Q(first_name__icontains=search) |
        Q(last_name__icontains=search) |
        Q(employee_id__icontains=search) |
        Q(position__icontains=search)
    ).filter(employment_status='active')[:10]
    
    results = []
    for staff in staff_list:
        results.append({
            'id': staff.id,
            'name': staff.full_name,
            'position': staff.position,
            'department': staff.department,
            'employee_id': staff.employee_id,
        })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def staff_update_status(request, staff_id):
    """Vista AJAX para actualizar estado de empleado"""
    try:
        staff = get_object_or_404(Staff, id=staff_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Staff.EMPLOYMENT_STATUS_CHOICES):
            staff.employment_status = new_status
            staff.save()
            
            return JsonResponse({
                'success': True,
                'message': _('Estado actualizado exitosamente.'),
                'new_status': staff.get_employment_status_display()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': _('Estado no válido.')
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 