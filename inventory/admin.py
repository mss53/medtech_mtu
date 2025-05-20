from django.contrib import admin
from .models import Category, Supplier, Warehouse, Item, Stock, Receipt, Move, WriteOff

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_info']

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'location']

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['item', 'warehouse', 'quantity']

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['item', 'warehouse', 'supplier', 'quantity', 'date', 'user']

@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ['item', 'from_warehouse', 'to_warehouse', 'quantity', 'date', 'user']

@admin.register(WriteOff)
class WriteOffAdmin(admin.ModelAdmin):
    list_display = ['item', 'warehouse', 'quantity', 'reason', 'date', 'user']
admin.site.site_header = "Материально-технический учёт ООО «Медтех»"
admin.site.site_title = "МТУ | ООО «Медтех»"
admin.site.index_title = "Панель управления"
