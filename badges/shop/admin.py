from django.contrib import admin
from .models import ShopItem, Purchase


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'price', 'quantity', 'is_available')
    list_filter = ('item_type', 'is_available')
    list_editable = ('price', 'quantity', 'is_available', 'item_type')
    search_fields = ('name',)
    filter_horizontal = ('allowed_roles',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'price_at_moment', 'purchased_at', 'status')
    list_filter = ('purchased_at', 'status')
    readonly_fields = ('purchased_at',)
