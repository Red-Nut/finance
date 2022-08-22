from django.contrib import admin

from .models import *

# Register your models here.
class AllocationCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
admin.site.register(AllocationCategory, AllocationCategoryAdmin)

class AllocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "description")
admin.site.register(Allocation, AllocationAdmin)

admin.site.register(Bank)

class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "bank", "account_no", "bsb")
admin.site.register(Account, AccountAdmin)

class AccountAccessAdmin(admin.ModelAdmin):
    list_display = ("account", "user")
admin.site.register(AccountAccess, AccountAccessAdmin)

class BudgetAdmin(admin.ModelAdmin):
    list_display = ("allocation", "basis", "value", "account", "rollover", "excess_to_allocation")
admin.site.register(Budget, BudgetAdmin)

class BudgetLockAdmin(admin.ModelAdmin):
    list_display = ("year", "month", "allocation", "basis", "value", "account", "rollover", "excess_to_allocation")
admin.site.register(BudgetLock, BudgetLockAdmin)



class AllocationsInlineAdmin(admin.TabularInline):
    model = TransactionAllocation

class CapexAllocationsInlineAdmin(admin.TabularInline):
    model = TransactionCapex

class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "name", "type", "value", "merchant", "paid_from", "paid_to", "comment")
    inlines = [AllocationsInlineAdmin, CapexAllocationsInlineAdmin]
admin.site.register(Transaction, TransactionAdmin)



class AllocationTransferAdmin(admin.ModelAdmin):
    list_display = ("from_allocation", "to_allocation", "value", "transaction")
admin.site.register(AllocationTransfer, AllocationTransferAdmin)

class TransactionAllocationAdmin(admin.ModelAdmin):
    list_display = ("transaction", "allocation", "value")
admin.site.register(TransactionAllocation, TransactionAllocationAdmin)


class CapexItemsInlineAdmin(admin.TabularInline):
    model = CapexItems
class CapexApprovalInlineAdmin(admin.TabularInline):
    model = CapexApproval

class CapexAdmin(admin.ModelAdmin):
    list_display = ("status", "name", "description", "paid_from")
    inlines = [CapexItemsInlineAdmin, CapexApprovalInlineAdmin]
admin.site.register(Capex, CapexAdmin)


class TransactionCapexAdmin(admin.ModelAdmin):
    list_display = ("transaction", "capex", "value")
admin.site.register(TransactionCapex, TransactionCapexAdmin)
