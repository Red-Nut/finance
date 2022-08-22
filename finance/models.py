from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class AllocationCategory(models.Model):
    name=models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"

class Allocation(models.Model):
    code = models.CharField(max_length=5)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, null=True, blank=True)
    category = models.ForeignKey(AllocationCategory, on_delete=models.RESTRICT, related_name="allocations")

    def __str__(self):
        return f"{self.code}: {self.name}"

class Bank(models.Model):
    name=models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"

class Account(models.Model):
    name = models.CharField(max_length=255)
    bank = models.ForeignKey(Bank, on_delete=models.RESTRICT)
    account_no = models.IntegerField()
    bsb = models.IntegerField()

    def __str__(self):
        return f"{self.name}"

class AccountAccess(models.Model):
    account = models.ForeignKey(Account, on_delete=models.RESTRICT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Budget(models.Model):
    WEEK = 1
    FORTNIGHT = 2
    MONTH = 3
    QUARTER = 4
    ANNUAL = 5
    BASIS = (
        (WEEK, _('Weekly')),
        (FORTNIGHT, _('Fortnightly')),
        (MONTH, _('Monthly')),
        (QUARTER, _('Quarterly')),
        (ANNUAL, _('Annually')),
    )

    allocation = models.OneToOneField(Allocation, on_delete=models.RESTRICT, related_name="budget")
    basis = models.PositiveSmallIntegerField(choices=BASIS)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.RESTRICT)
    rollover = models.BooleanField()
    excess_to_allocation = models.ForeignKey(Allocation, null=True, blank=True, on_delete=models.RESTRICT, related_name="excess")

    def __str__(self):
        return f"{self.allocation}: {self.value} {self.basis}"

class BudgetLock(models.Model):
    JAN = 1
    FEB = 2
    MAR = 3
    APR = 4
    MAY = 5
    JUN = 6
    JUL = 7
    AUG = 8
    SEP = 9
    OCT = 10
    NOV = 11
    DEC = 12
    MONTHS = (
        (JAN, _('January')),
        (FEB, _('February')),
        (MAR, _('March')),
        (APR, _('April')),
        (MAY, _('May')),
        (JUN, _('June')),
        (JUL, _('July')),
        (AUG, _('August')),
        (SEP, _('September')),
        (OCT, _('October')),
        (NOV, _('November')),
        (DEC, _('December')),
    )

    WEEK = 1
    FORTNIGHT = 2
    MONTH = 3
    QUARTER = 4
    ANNUAL = 5
    BASIS = (
        (WEEK, _('Weekly')),
        (FORTNIGHT, _('Fortnightly')),
        (MONTH, _('Monthly')),
        (QUARTER, _('Quarterly')),
        (ANNUAL, _('Annually')),
    )

    year = models.IntegerField()
    month = models.PositiveSmallIntegerField(choices=MONTHS)
    allocation = models.ForeignKey(Allocation, on_delete=models.RESTRICT, related_name="budget_lock")
    basis = models.PositiveSmallIntegerField(choices=BASIS)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.RESTRICT)
    rollover = models.BooleanField()
    excess_to_allocation = models.ForeignKey(Allocation, null=True, blank=True, on_delete=models.RESTRICT, related_name="excess_lock")


class Transaction(models.Model):
    CREDIT = 1
    DEBIT = 2
    TRANSFER = 3 # Credit 
    TRANSFER_DUPLICATE = 4 # Debit
    EXCESS = 5
    BUDGET = 6
    TYPE = (
        (CREDIT, _('Credit')),
        (DEBIT, _('Debit')),
        (TRANSFER, _('Transfer')),
        (TRANSFER_DUPLICATE, _('Transfer Duplicate')),
        (EXCESS, _('Excess Funds Reallocated')),
        (BUDGET, _('Budget Allocation')),
    )

    date = models.DateField()
    name = models.CharField(max_length=255)
    merchant = models.CharField(max_length=255, null=True, blank=True)
    paid_to = models.ForeignKey(
        Account, 
        null=True, 
        blank=True, 
        on_delete=models.RESTRICT, 
        related_name="transaction_from"
    )
    paid_from = models.ForeignKey(
        Account, 
        null=True, 
        blank=True, 
        on_delete=models.RESTRICT,
        related_name="transaction_to"
    )
    type = models.PositiveSmallIntegerField(choices=TYPE)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    comment = models.CharField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.date})"

class AllocationTransfer(models.Model):
    from_allocation = models.ForeignKey(Allocation, on_delete=models.CASCADE, related_name="transfers_from")
    to_allocation = models.ForeignKey(Allocation, on_delete=models.CASCADE, related_name="transfers_to")
    value = models.DecimalField(max_digits=8, decimal_places=2)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)

class Capex(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000)
    paid_from = models.ForeignKey(Allocation, on_delete=models.RESTRICT)

    def __str__(self):
        return f"{self.name}"
	
class CapexItems(models.Model):
    capex = models.ForeignKey(Capex, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=255)
    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    dateEstimate = models.DateField(null=True, blank=True)
    link = models.URLField(max_length=1000, null=True, blank=True)
    comment = models.CharField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class CapexApproval(models.Model):
    DRAFT = 0
    REQUESTED = 1
    APPROVED = 2
    CLOSED = 3
    STATUS = (
        (DRAFT, _('Draft')),
        (REQUESTED, _('Requested')),
        (APPROVED, _('Approved')),
        (CLOSED, _('Closed')),
    )

    capex = models.OneToOneField(Capex, on_delete=models.RESTRICT, related_name="status")
    status = models.PositiveSmallIntegerField(choices=STATUS)
    requested_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="capex_requester")
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.RESTRICT, related_name="capex_approver")
    requested_date = models.DateField()
    approved_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_status_display()}"

class TransactionCapex(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="capex_allocation")
    capex = models.ForeignKey(Capex, on_delete=models.RESTRICT, related_name="transactions")
    value = models.DecimalField(max_digits=8, decimal_places=2)

class TransactionAllocation(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="allocations")
    allocation = models.ForeignKey(Allocation, on_delete=models.RESTRICT, related_name="transactions")
    value = models.DecimalField(max_digits=8, decimal_places=2)


