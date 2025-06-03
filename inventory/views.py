from django.db import models
from datetime import datetime, timedelta, date
from .models import ItemCard, MaintenanceSchedule, Movement, Warehouse, User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from .forms import MovementForm, MaintenanceScheduleForm
import openpyxl
from django.http import HttpResponse
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from .procurement import PurchaseRequest, RequestStatus, Supplier, PurchaseOrder, PurchaseRequestItem
from django.forms import modelformset_factory
from .forms import PurchaseRequestForm, PurchaseRequestItemForm, PurchaseOrderForm, PurchaseRequestStatusForm





def is_warehouseman(user):
    return user.is_superuser or user.groups.filter(name='Кладовщик').exists()
    
def stock_list(request):
    # Получить все карточки с ненулевым количеством (текущие запасы)
    qs = ItemCard.objects.filter(quantity__gt=0).select_related(
        'item', 'warehouse', 'location'
    ).order_by('warehouse__name', 'location__code', 'item__name')

    # Фильтрация по складу, ячейке, названию товара через параметры GET (например, ?warehouse=2)
    warehouse_id = request.GET.get('warehouse')
    location_id = request.GET.get('location')
    item_id = request.GET.get('item')

    if warehouse_id:
        qs = qs.filter(warehouse_id=warehouse_id)
    if location_id:
        qs = qs.filter(location_id=location_id)
    if item_id:
        qs = qs.filter(item_id=item_id)

    context = {
        'stocks': qs,
        # Для фильтров:
        'warehouses': set(card.warehouse for card in qs),
        'locations': set(card.location for card in qs if card.location),
        'items': set(card.item for card in qs),
    }
    return render(request, 'inventory/stock_list.html', context)

def upcoming_maintenance(request):
    today = date.today()
    threshold = today + timedelta(days=14)  # Сколько дней до срока считается "напоминанием"
    schedules = MaintenanceSchedule.objects.filter(next_due_date__lte=threshold, next_due_date__gte=today)
    return render(request, 'inventory/upcoming_maintenance.html', {'schedules': schedules})

@login_required(login_url='/login/')
def home(request):
    user = request.user
    is_storekeeper = user.groups.filter(name="Кладовщик").exists()
    is_maintenance = user.groups.filter(name="Ответственный по ТО").exists()
    is_procurement = user.groups.filter(name="Снабженец").exists()
    is_manager = user.groups.filter(name="Руководитель").exists()

    context = {
        'user': user,
        'is_storekeeper': is_storekeeper,
        'is_maintenance': is_maintenance,
        'is_procurement': is_procurement,
        'is_manager': is_manager,
    }
    return render(request, 'inventory/home.html', context)

class MyLoginView(LoginView):
    template_name = 'inventory/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

@login_required
def movements_list(request):
    movements = Movement.objects.select_related(
        'item_card', 'from_warehouse', 'to_warehouse',
        'from_department', 'to_department', 'user'
    ).order_by('-date')

    # Получаем параметры из формы (GET-запроса)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    warehouse_id = request.GET.get('warehouse')
    op_type = request.GET.get('type')

    # --- Вставь вот этот фильтр сразу после получения переменных! ---
    if start_date and start_date not in ('', 'None'):
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            movements = movements.filter(date__gte=start_dt)
        except Exception as e:
            print("Ошибка start_date:", e)
    if end_date and end_date not in ('', 'None'):
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            movements = movements.filter(date__lt=end_dt)
        except Exception as e:
            print("Ошибка end_date:", e)
    # ---------------------------------------------------------------

    if warehouse_id and warehouse_id not in ('', 'None'):
        movements = movements.filter(
            models.Q(from_warehouse_id=warehouse_id) | models.Q(to_warehouse_id=warehouse_id)
        )
    if op_type and op_type not in ('', 'None'):
        movements = movements.filter(type=op_type)

    warehouses = Warehouse.objects.all()

    context = {
        'movements': movements[:100],
        'warehouses': warehouses,
        'selected_warehouse': warehouse_id,
        'selected_type': op_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'inventory/movements_list.html', context)

@login_required
def movement_create(request):
    if request.method == "POST":
        form = MovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.user = request.user
            movement.save()
            return redirect('movements')
    else:
        form = MovementForm()
    return render(request, 'inventory/movement_form.html', {'form': form})
    
@login_required
def export_movements_excel(request):
    movements = Movement.objects.select_related(
        'item_card', 'from_warehouse', 'to_warehouse',
        'from_department', 'to_department', 'user'
    ).order_by('-date')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    warehouse_id = request.GET.get('warehouse')
    op_type = request.GET.get('type')

    # Корректная фильтрация
    if start_date and start_date not in ('', 'None'):
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            movements = movements.filter(date__gte=start_dt)
        except Exception:
            pass

    if end_date and end_date not in ('', 'None'):
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            movements = movements.filter(date__lt=end_dt)
        except Exception:
            pass

    if warehouse_id and warehouse_id not in ('', 'None'):
        movements = movements.filter(
            models.Q(from_warehouse_id=warehouse_id) | models.Q(to_warehouse_id=warehouse_id)
        )
    if op_type and op_type not in ('', 'None'):
        movements = movements.filter(type=op_type)

    # Формируем Excel-файл
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Движения МТС"

    headers = [
        "Дата", "Тип", "МТС", "Серийный номер", "Партия", "Кол-во",
        "Откуда", "Куда", "Ответственный", "Комментарий"
    ]
    ws.append(headers)

    for m in movements:
        from_str = ""
        to_str = ""
        if m.from_warehouse:
            from_str += m.from_warehouse.name
        if m.from_department:
            from_str += f" ({m.from_department.name})"
        if m.to_warehouse:
            to_str += m.to_warehouse.name
        if m.to_department:
            to_str += f" ({m.to_department.name})"
        ws.append([
            m.date.strftime("%d.%m.%Y %H:%M"),
            m.get_type_display(),
            m.item_card.item.name if m.item_card else "",
            m.item_card.serial_number if m.item_card else "",
            m.item_card.batch if m.item_card else "",
            m.quantity,
            from_str,
            to_str,
            m.user.get_full_name() if m.user else "",
            m.comment
        ])

    # Отправляем файл пользователю
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=movements.xlsx'
    wb.save(response)
    return response

@login_required
def add_maintenance(request):
    if request.method == 'POST':
        form = MaintenanceScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('upcoming_maintenance')
    else:
        form = MaintenanceScheduleForm()
    return render(request, 'inventory/add_maintenance.html', {'form': form})
    
@login_required
def upcoming_maintenance(request):
    today = date.today()
    threshold = today + timedelta(days=14)
    schedules = MaintenanceSchedule.objects.filter(
        next_due_date__lte=threshold,
        next_due_date__gte=today
    )

    responsible_id = request.GET.get('responsible')
    maint_type = request.GET.get('type')

    if responsible_id and responsible_id != '':
        schedules = schedules.filter(responsible_id=responsible_id)
    if maint_type and maint_type != '':
        schedules = schedules.filter(maintenance_type=maint_type)

    # Для фильтра
    responsibles = User.objects.filter(id__in=schedules.values_list('responsible_id', flat=True))
    maint_types = MaintenanceSchedule._meta.get_field('maintenance_type').choices

    return render(request, 'inventory/upcoming_maintenance.html', {
        'schedules': schedules,
        'today': today,
        'responsibles': responsibles,
        'maint_types': maint_types,
        'selected_type': maint_type,
        'selected_responsible': responsible_id,
    })

@login_required
def send_maintenance_reminder(request, schedule_id):
    schedule = get_object_or_404(MaintenanceSchedule, id=schedule_id)
    user = schedule.responsible

    if user.email:
        subject = 'Напоминание о проведении ТО'
        message = (
            f'Уважаемый {user.get_full_name() or user.username},\n\n'
            f'Необходимо провести техническое обслуживание по объекту: {schedule.item_card}.\n'
            f'Тип обслуживания: {schedule.get_maintenance_type_display()}.\n'
            f'Дата проведения: {schedule.next_due_date.strftime("%d.%m.%Y")}.\n\n'
            'Пожалуйста, выполните необходимые работы или свяжитесь с ответственным лицом.'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, f'Напоминание отправлено на {user.email}.')
    else:
        messages.error(request, f'У пользователя {user.username} не указан email.')

    return redirect('upcoming_maintenance')

@login_required
def purchase_requests_list(request):
    # Фильтрация по статусу, департаменту, дате
    status = request.GET.get('status')
    department = request.GET.get('department')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    queryset = PurchaseRequest.objects.all().select_related('department', 'created_by')

    if status:
        queryset = queryset.filter(status=status)
    if department:
        queryset = queryset.filter(department_id=department)
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    departments = queryset.model._meta.get_field('department').related_model.objects.all()
    statuses = RequestStatus.choices

    context = {
        'requests': queryset.order_by('-created_at'),
        'departments': departments,
        'statuses': statuses,
        'selected_status': status,
        'selected_department': department,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'inventory/purchase_requests_list.html', context)
    
@login_required
def purchase_request_create(request):
    ItemFormSet = modelformset_factory(PurchaseRequestItem, form=PurchaseRequestItemForm, extra=1, can_delete=True)
    if request.method == "POST":
        form = PurchaseRequestForm(request.POST)
        formset = ItemFormSet(request.POST, queryset=PurchaseRequestItem.objects.none())
        if form.is_valid() and formset.is_valid():
            purchase_request = form.save(commit=False)
            purchase_request.created_by = request.user
            purchase_request.save()
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                    item = item_form.save(commit=False)
                    item.request = purchase_request
                    item.save()
            return redirect('purchase_request_detail', pk=purchase_request.id)
    else:
        form = PurchaseRequestForm()
        formset = ItemFormSet(queryset=PurchaseRequestItem.objects.none())
    return render(request, 'inventory/purchase_request_form.html', {'form': form, 'formset': formset})

@login_required
def purchase_request_edit(request, pk):
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk)
    ItemFormSet = modelformset_factory(PurchaseRequestItem, form=PurchaseRequestItemForm, extra=0, can_delete=True)
    if request.method == "POST":
        form = PurchaseRequestForm(request.POST, instance=purchase_request)
        formset = ItemFormSet(request.POST, queryset=purchase_request.items.all())
        if form.is_valid() and formset.is_valid():
            form.save()
            for item_form in formset:
                if item_form.cleaned_data:
                    if item_form.cleaned_data.get('DELETE'):
                        if item_form.instance.pk:
                            item_form.instance.delete()
                    else:
                        item = item_form.save(commit=False)
                        item.request = purchase_request
                        item.save()
            return redirect('purchase_request_detail', pk=purchase_request.id)
    else:
        form = PurchaseRequestForm(instance=purchase_request)
        formset = ItemFormSet(queryset=purchase_request.items.all())
    return render(request, 'inventory/purchase_request_form.html', {'form': form, 'formset': formset, 'edit_mode': True})

@login_required
def purchase_request_detail(request, pk):
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == 'POST':
        status_form = PurchaseRequestStatusForm(request.POST, instance=purchase_request)
        if status_form.is_valid():
            status_form.save()
            messages.success(request, "Статус заявки успешно обновлен.")
            return redirect('purchase_request_detail', pk=pk)
    else:
        status_form = PurchaseRequestStatusForm(instance=purchase_request)
    return render(request, 'inventory/purchase_request_detail.html', {
        'purchase_request': purchase_request,
        'status_form': status_form,
    })
    
@login_required
def create_purchase_order(request, pk):
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == "POST":
        form = PurchaseOrderForm(request.POST, request.FILES)
        if form.is_valid():
            order = form.save(commit=False)
            order.request = purchase_request
            order.save()
            purchase_request.status = 'ordered'
            purchase_request.save()
            return redirect('purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderForm()
    return render(request, 'inventory/create_purchase_order.html', {
        'form': form,
        'purchase_request': purchase_request,
    })

@login_required
def purchase_order_detail(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, 'inventory/purchase_order_detail.html', {'order': order})
    
def itemcard_detail(request, pk):
    item_card = get_object_or_404(ItemCard, pk=pk)
    event_type = request.GET.get('event_type')
    event_logs = item_card.event_logs.all()
    if event_type:
        event_logs = event_logs.filter(event_type=event_type)
    return render(request, 'inventory/itemcard_detail.html', {
        'item_card': item_card,
        'event_logs': event_logs,
        'selected_event_type': event_type,
    })


# Create your views here.

