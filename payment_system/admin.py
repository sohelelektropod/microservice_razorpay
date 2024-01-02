from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('payment_id','amount', 'payment_method', 'status', 'created_at', 'updated_at')
