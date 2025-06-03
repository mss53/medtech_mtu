from django import forms
from .models import Movement, Department, Item
from .maintenance import MaintenanceSchedule
from .procurement import PurchaseRequest, PurchaseRequestItem, PurchaseOrder, RequestStatus


class MaintenanceScheduleForm(forms.ModelForm):
    class Meta:
        model = MaintenanceSchedule
        fields = ['item_card', 'maintenance_type', 'next_due_date', 'interval_days', 'responsible', 'comment']
        widgets = {
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class MovementForm(forms.ModelForm):
    class Meta:
        model = Movement
        fields = [
            'item_card', 'from_warehouse', 'to_warehouse',
            'from_department', 'to_department', 'quantity',
            'type', 'comment'
        ]
        widgets = {
            'type': forms.Select(choices=Movement._meta.get_field('type').choices),
            'comment': forms.Textarea(attrs={'rows': 2}),
        }

class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['department', 'comment']

class PurchaseRequestItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestItem
        fields = ['item', 'quantity', 'comment']

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'contract_number', 'contract_file', 'comment']
        

class PurchaseRequestStatusForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['status']
        labels = {'status': 'Статус заявки'}

