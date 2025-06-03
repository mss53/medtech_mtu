from django.contrib import admin
from .models import Category, Department, Warehouse, Item, ItemCard, Movement, Location, InventorySession, InventoryRecord, MaintenanceSchedule, MaintenanceLog, PurchaseRequest, PurchaseRequestItem, PurchaseOrder, Supplier
from .admin_actions import export_inventory_to_excel
from .commissioning import CommissioningAct

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'code', 'description']
    list_filter = ['warehouse']

@admin.register(InventorySession)
class InventorySessionAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'date_started', 'date_finished', 'status']
    list_filter = ['warehouse', 'status']
    actions = [export_inventory_to_excel]

@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = ['session', 'item_card', 'location', 'quantity_fact', 'quantity_system', 'difference']
    list_filter = ['session', 'location']
    search_fields = ['item_card__item__name', 'item_card__serial_number', 'item_card__batch']
    readonly_fields = ('difference',)  # это поле нельзя править вручную
    actions = [export_inventory_to_excel]
    

class CommissioningActInline(admin.TabularInline):
    model = CommissioningAct
    extra = 1
    
@admin.register(ItemCard)
class ItemCardAdmin(admin.ModelAdmin):
    list_display = ['item', 'serial_number', 'batch', 'purchase_order', 'warehouse', 'department', 'quantity', 'expiration_date']
    search_fields = ['item__name', 'purchase_order__contract_number', 'purchase_order__supplier__name' 'serial_number', 'batch']
    list_filter = ['item__category', 'warehouse', 'purchase_order',  'department', 'expiration_date']
    inlines = [CommissioningActInline]  # Добавь сюда Inline

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ['item_card', 'type', 'from_warehouse', 'to_warehouse', 'from_department', 'to_department', 'quantity', 'date', 'user']
    search_fields = ['item_card__item__name', 'item_card__serial_number', 'item_card__batch']
    list_filter = ['type', 'from_warehouse', 'to_warehouse', 'from_department', 'to_department', 'date']

admin.site.register(Category)
admin.site.register(Department)
admin.site.register(Warehouse)
admin.site.register(Item)

admin.site.site_header = "Материально-технический учёт ООО «Медтех»"
admin.site.site_title = "МТУ | ООО «Медтех»"
admin.site.index_title = "Панель управления"

@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('item_card', 'maintenance_type', 'next_due_date', 'responsible')
    list_filter = ('maintenance_type', 'responsible', 'next_due_date')
    search_fields = ('item_card__item__name', 'item_card__serial_number')

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'date_performed', 'performed_by', 'result')
    list_filter = ('schedule__maintenance_type', 'performed_by')
    search_fields = ('schedule__item_card__item__name', 'schedule__item_card__serial_number')

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'department', 'created_at', 'status', 'approver', 'approved_at')
    list_filter = ('status', 'department')
    search_fields = ('id', 'department__name')
    inlines = [type('PurchaseRequestItemInline', (admin.TabularInline,), {'model': PurchaseRequestItem, 'extra': 0})]

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'request', 'created_at', 'status')
    list_filter = ('status', 'supplier')
    search_fields = ('id', 'supplier__name', 'request__id')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_info')

@admin.register(CommissioningAct)
class CommissioningActAdmin(admin.ModelAdmin):
    list_display = ('item_card', 'act_number', 'date_commissioned')
    list_filter = ('date_commissioned',)
    search_fields = ('act_number', 'item_card__item__name', 'item_card__serial_number')
