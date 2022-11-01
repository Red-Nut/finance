from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F, Min

from finance.models import AllocationCategory, BudgetLock, Transaction, TransactionAllocation

# This module imports.
from .models import *
from .models import Budget

# Third party imports.
import json
import datetime
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import locale

from django.views.generic import TemplateView

def Update(request):

    return redirect('index')

def LockBudget(request, year, month):
    budgets = Budget.objects.all()
    for budget in budgets:
        budgetLock = BudgetLock.objects.create(
            year = year,
            month = month,
            allocation = budget.allocation,
            basis = budget.basis,
            value = budget.value,
            account = budget.account,
            rollover = budget.rollover,
            excess_to_allocation = budget.excess_to_allocation
        )

    budgetLocks = BudgetLock.objects.filter(year=year,month=month).all()

    firstDayOfMonth = datetime.date(year,month,1)

    for budget in budgetLocks:
        if budget.basis == budget.WEEK:
            for w in range(5):
                # Week Start Date
                if w == 0:
                    weekStart = FirstMonday(firstDayOfMonth)
                else: 
                    weekStart = FirstMonday(firstDayOfMonth) + datetime.timedelta(days=(7*w))

                # exit if week is outside of the month (i.e week 5)
                if w != 0:
                    if weekStart.month != firstDayOfMonth.month:
                        break

                # Add transaction
                transaction = Transaction.objects.create(
                    date=weekStart,
                    name=f"Budget Allocation: {budget.allocation.code} ({budget.allocation.name})",
                    type=Transaction.BUDGET,
                    value=budget.value
                )

                transactionAllocation = TransactionAllocation.objects.create(
                    transaction=transaction,
                    allocation=budget.allocation,
                    value=budget.value
                )

        else:
            if budget.basis == budget.FORTNIGHT:
                value=budget.value*4.3/2
            if budget.basis == budget.MONTH:
                value=budget.value
            if budget.basis == budget.QUARTER:
                value=budget.value/3
            if budget.basis == budget.ANNUAL:
                value=budget.value/12
            # Add transaction
            transaction = Transaction.objects.create(
                date=firstDayOfMonth,
                name=f"Budget Allocation: {budget.allocation.code} ({budget.allocation.name})",
                type=Transaction.BUDGET,
                value=budget.value
            )
            
            transactionAllocation = TransactionAllocation.objects.create(
                transaction=transaction,
                allocation=budget.allocation,
                value=value
            )


    return redirect('index')

# Index.
def Index(request):
    myDate = datetime.date.today()

    return redirect(reverse('dashboard', kwargs={'year':myDate.year, 'month':myDate.month, 'day':myDate.day}))    

def Dashboard(request, year, month, day):
    myDate = datetime.date(year,month,day)
    currentWeekDate = myDate # For tracking week number

    # Stay in previous month until the final week is completed.
    weekBasisStart = FirstMonday(myDate)
    if weekBasisStart > myDate:
        myDate = myDate - relativedelta(months=1)
        weekBasisStart = FirstMonday(myDate)

    year = myDate.year
    month = myDate.month
    day = myDate.day

    weekBasisEnd = weekBasisStart + relativedelta(weeks=4) + relativedelta(days=1)
    if weekBasisEnd.month == weekBasisStart.month:
        weekBasisEnd = weekBasisStart + relativedelta(weeks=5) - relativedelta(days=1)
    else: 
        weekBasisEnd = weekBasisStart + relativedelta(weeks=4) - relativedelta(days=1)


    monthStart = datetime.date(year,month,1)
    monthRange = monthrange(year, month)
    monthEnd = datetime.date(year,month, monthRange[1])

    # INCOME
    incomeCategory = AllocationCategory.objects.get(id=11)

    # income
    query = TransactionAllocation.objects.filter(allocation__category=incomeCategory).all()
    query = query.filter(transaction__date__range=[monthStart.strftime("%Y-%m-%d"), monthEnd.strftime("%Y-%m-%d")]).all()
    query = query.aggregate(Sum('value'))
    value = query["value__sum"]
    if value is None:
        value = 0
    else:
        value = float(value)
    
    # Debits
    query = TransactionAllocation.objects.exclude(allocation__category=incomeCategory).all()
    query = query.filter(transaction__type=Transaction.DEBIT).all()
    query = query.filter(transaction__date__range=[monthStart.strftime("%Y-%m-%d"), monthEnd.strftime("%Y-%m-%d")]).all()
    query = query.aggregate(Sum('value'))
    debits = query["value__sum"]
    if debits is None:
        debits = 0
    else:
        debits = float(-debits)

    # Credits
    query = TransactionAllocation.objects.exclude(allocation__category=incomeCategory).all()
    query = query.filter(transaction__type=Transaction.CREDIT).all()
    query = query.filter(transaction__date__range=[monthStart.strftime("%Y-%m-%d"), monthEnd.strftime("%Y-%m-%d")]).all()
    query = query.aggregate(Sum('value'))
    credits = query["value__sum"]
    if credits is None:
        credits = 0
    else:
        credits = float(credits)

    # Budget
    query = TransactionAllocation.objects.exclude(allocation__category=incomeCategory).all()
    query = query.filter(transaction__type=Transaction.BUDGET).all()
    query = query.filter(transaction__date__range=[monthStart.strftime("%Y-%m-%d"), monthEnd.strftime("%Y-%m-%d")]).all()
    query = query.aggregate(Sum('value'))
    budget = query["value__sum"]
    if budget is None:
        budget = 0
    else:
        budget = float(budget)

    income = {
        "value" : value,
        "debits" : debits,
        "credits" : credits,
        "net" : debits-credits,
        "budget" : budget,
    }

    # Savings
    savings = SavingCreation(year,month)

    savingsHistory = []
    for i in range(6):
        x=5-i
        endDate = monthEnd - relativedelta(months=x)
        saving = SavingCreation(endDate.year,endDate.month)

        savingsHistory.append(saving)
    
    # CAPEX
    capexes = Capex.objects.all().filter(transactions__isnull=False).distinct()
    capexes = capexes.exclude(status__status=CapexApproval.CLOSED)
    capexes = capexes.annotate(budget=Sum(F('items__price')*F('items__qty'), distinct = True))
    capexes = capexes.annotate(spent=Sum(F('transactions__value')*-1, distinct = True))
    capexes = capexes.annotate(remaining=Sum(F('items__price')*F('items__qty'), distinct = True)+Sum(F('transactions__value'), distinct = True))
    
    
    # WEEKLY
    weeks = []
    currentWeekNo = None
    for w in range(5):
        # Date Range
        if w == 0:
            weekStart = FirstMonday(myDate)
        else: 
            weekStart = weeks[w-1]['weekStart'] + datetime.timedelta(days=7)

        # exit if week is outside of the month (i.e week 5)
        if w != 0:
            if weekStart.month != weeks[0]['weekStart'].month:
                break

        weekEnd = weekStart + datetime.timedelta(days=6)

        if currentWeekDate >= weekStart and currentWeekDate <= weekEnd:
            currentWeekNo = w

        # Transaction list
        transactions = TransactionAllocation.objects.all()
        transactions = transactions.filter(transaction__date__range=[weekStart.strftime("%Y-%m-%d"), weekEnd.strftime("%Y-%m-%d")]).all()
        transactionsCapex = TransactionCapex.objects.all()
        transactionsCapex = transactionsCapex.filter(transaction__date__range=[weekStart.strftime("%Y-%m-%d"), weekEnd.strftime("%Y-%m-%d")]).all()

        # Allocations
        allocationsQuery = Allocation.objects.all()
        allocations = []
        allocationsGraph = []
        for a in allocationsQuery:
            allocation = AllocationCreation(a, weekStart, weekEnd, year, month)

            # Excess Percentage Cap
            if (allocation["excess"] + allocation["budget"]) > allocation["budget"]*3:
                excessPercentCapped = 300
            else:
                excessPercentCapped = allocation["excess"] 
            allocation["excessPercentCapped"] = excessPercentCapped

            allocations.append(allocation)

            # Allocations to graph
            include = False
            try:
                if a.budget.basis == Budget.WEEK:
                    include = True
            except:
                pass

            if(a.category.id != 9 and a.category.id != 10 and a.category.id != 11):
                if include:
                    allocationsGraph.append(allocation)

        # Categories
        categoriesQuery = AllocationCategory.objects.all()
        categories = []
        categoriesGraph = []
        for c in categoriesQuery:
            category = CategoryCreation(c, allocations, weekStart, weekEnd, year, month)
            categories.append(category)

            # Categories to graph
            include = False
            for allocation in c.allocations.all():
                try:
                    if allocation.budget.basis == Budget.WEEK:
                        include = True
                except:
                    pass

            if(c.id != 9 and c.id != 10 and c.id != 11):
                if include:
                    categoriesGraph.append(category)

        

            

        # Allocation Grouping for graph
        gap = False
        x = 1
        prevCat = allocationsGraph[0]["object"].category
        for a in allocationsGraph:
            c = a["object"].category
            if(c != prevCat):
                x = x + 1
            a["x"] = x

            prevCat = a["object"].category
            x = x + 1

        # create the week object
        week = {
            "weekNo": w,
            "weekNoDisplay": w+1,
            "weekStart" : weekStart,
            "weekEnd" : weekEnd,
            "transactions" : transactions,
            "categories" : categories,
            "categoriesGraph" : categoriesGraph,
            "allocations" : allocations,
            "allocationsGraph" : allocationsGraph,
        }

        weeks.append(week)

    for w in range(len(weeks)):
        
        weeks[w]['weekStart'] = weeks[w]['weekStart'].strftime("%B %d, %Y")
        weeks[w]['weekEnd'] = weeks[w]['weekEnd'].strftime("%B %d, %Y")

    currentWeek = weeks[currentWeekNo]

    
    # MONTHLY

    # Transactions
    transactions = TransactionAllocation.objects.all()
    transactions = transactions.filter(transaction__date__range=[monthStart.strftime("%Y-%m-%d"), monthEnd.strftime("%Y-%m-%d")]).all()
    transactionsCapex = TransactionCapex.objects.all()
    transactionsCapex = transactionsCapex.filter(transaction__date__range=[monthStart.strftime("%Y-%m-%d"), monthEnd.strftime("%Y-%m-%d")]).all()

    # Allocations
    allocationsQuery = Allocation.objects.all()
    allocations = []
    allocationsGraph=[]
    for a in allocationsQuery:
        try:
            if a.budget.basis == Budget.WEEK:
                allocation = AllocationCreation(a, weekBasisStart, weekBasisEnd, year, month)
            else: 
                allocation = AllocationCreation(a, monthStart, monthEnd, year, month)
        except: 
            allocation = AllocationCreation(a, monthStart, monthEnd, year, month)
        allocations.append(allocation)

        # Allocations to graph
        #include = False
        #try:
        #    if a.budget.basis == Budget.WEEK or a.budget.basis == Budget.FORTNIGHT or a.budget.basis == Budget.MONTH:
        #        include = True
        #except:
        #    pass

        if(a.category.id != 9 and a.category.id != 10 and a.category.id != 11):
            #if include:
            allocationsGraph.append(allocation)

    # Allocation Grouping for graph
    gap = False
    x = 1
    prevCat = allocationsGraph[0]["object"].category
    for a in allocationsGraph:
        c = a["object"].category
        if(c != prevCat):
            x = x + 1
        a["x"] = x

        prevCat = a["object"].category
        x = x + 1                

    # Categories
    categoriesQuery = AllocationCategory.objects.all()
    categories = []
    categoriesGraph = []
    for c in categoriesQuery:
        category = CategoryCreation(c, allocations, monthStart, monthEnd, year, month)
        categories.append(category)

        # Categories to Graph
        if(c.id != 9 and c.id != 10 and c.id != 11):
            categoriesGraph.append(category)

    

    # Sort Lists
    #categories.sort(key=lambda x: x['spend'], reverse=True)

    context = {
        "currentMonth" : myDate.strftime("%B"),
        "currentYear" : myDate.strftime("%Y"),
        "monthStart" : monthStart.strftime("%B %d, %Y"),
        "monthEnd" : monthEnd.strftime("%B %d, %Y"),
        "weekBasisStart" : weekBasisStart.strftime("%B %d, %Y"),
        "weekBasisEnd" : weekBasisEnd.strftime("%B %d, %Y"),

        "income" : income,
        "savings" : savings,
        "savingsHistory" : savingsHistory,

        "capexes" : capexes,

        "weeks" : weeks,
        "currentWeek" : currentWeek,
        "currentWeekNo" : currentWeekNo,
        "currentWeekNoDisplay" : currentWeekNo+1,
        
        "transactions" : transactions,
        "categories" : categories,
        "categoriesGraph" : categoriesGraph,
        "allocationsGraph" : allocationsGraph,
        "allocations" : allocations,
    }

    return render(request, "dashboard.html", context)

def FirstMonday(myDate):
    startOfMonth = datetime.date(myDate.year,myDate.month,1)
    dayOfTheWeek = startOfMonth.weekday()
    dateOfFirstMonday = 8-dayOfTheWeek

    if dateOfFirstMonday == 8:
        dateOfFirstMonday = 1

    return datetime.date(myDate.year,myDate.month,dateOfFirstMonday)

def CategoryCreation(c, allocations, dateStart, dateEnd, year, month):
    budget = 0
    debits = 0
    credits = 0

    for allocation in allocations:
        if allocation["object"].category == c:
            budget += allocation["budget"]
            debits += allocation["debits"]
            credits += allocation["credits"]


    # Net Change
    budget = float(budget)
    net = float(credits - debits)
    spend = float(debits - credits)

    excess = float(0)
    under = float(0)
    if(spend > budget):
        excess = spend - budget
    else:
        under = budget - spend

    category = {
        "object" : c,
        "debits" : round(debits,2),
        "credits" : round(credits,2),
        "net" : round(net,2),
        "spend" : round(spend,2),
        "budget" : round(budget,2),
        "excess" : round(excess,2),
        "under" : round(under,2),   
    }

    return category

def AllocationCreation(a, dateStart, dateEnd, year, month):
    # Budget
    budget = 0

    budgetObject = BudgetLock.objects.filter(year=year).filter(month=month).filter(allocation=a).first()
    if budgetObject != None:
        # Rollover
        if budgetObject.rollover:
            # Filter allocation
            allocations = TransactionAllocation.objects.filter(allocation=a).all()
            # Filter to just Credits, Debits, Budget allocations and excess funds transfers
            allocations = allocations.exclude(transaction__type=Transaction.TRANSFER).all()
            allocations = allocations.exclude(transaction__type=Transaction.TRANSFER_DUPLICATE).all()
            # Fitler only transactions before start date
            thisDate = dateStart - relativedelta(days=1)
            allocations = allocations.filter(transaction__date__lte=thisDate.strftime("%Y-%m-%d")).all()
            
            # Add aggregate
            allocations = allocations.aggregate(Sum('value'))

            if allocations is not None:
                total = allocations["value__sum"]
                if total is not None:
                    budget += total

        #This period budget
        # Filter allocation
        allocations = TransactionAllocation.objects.filter(allocation=a).all()
        # Filter budget allocations
        allocations = allocations.filter(transaction__type=Transaction.BUDGET).all()
        # Filter date range for this period
        allocations = allocations.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")]).all()
        # Add aggregate
        allocations = allocations.aggregate(Sum('value'))   

        if allocations is not None:
            total = allocations["value__sum"]
            if total is not None:
                budget += total

    # Budget Reallocation
    query = TransactionAllocation.objects.filter(allocation=a)
    query = query.filter(transaction__type=Transaction.EXCESS)
    query = query.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")])
    query = query.aggregate(Sum('value'))
    reallocation = query["value__sum"]
    if reallocation is None:
        reallocation = 0
    else:
        reallocation = -reallocation
        budget -= reallocation
    
    # Debits
    query = TransactionAllocation.objects.filter(allocation=a)
    query = query.filter(transaction__type=Transaction.DEBIT)
    query = query.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")])
    query = query.aggregate(Sum('value'))
    debits = query["value__sum"]
    if debits is None:
        debits = 0
    else:
        debits = -debits

    
    
    # Credits
    query = TransactionAllocation.objects.filter(allocation=a)
    query = query.filter(transaction__type=Transaction.CREDIT)
    query = query.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")])
    query = query.aggregate(Sum('value'))
    credits = query["value__sum"]
    if credits is None:
        credits = 0

    # Net Change
    budget = float(budget)
    net = float(credits - debits)
    spend = float(debits - credits)
    reallocation = float(reallocation)

    excess = float(0)
    under = float(0)
    if(spend > budget):
        excess = spend - budget
    else:
        under = budget - spend

    # Budget Object
    budgetObject = BudgetLock.objects.filter(year=year).filter(month=month).filter(allocation=a).first()
    if budgetObject != None:
        pass

    allocation = {
        "object" : a,
        "debits" : round(debits,2),
        "credits" : round(credits,2),
        "net" : round(net,2),
        "spend" : round(spend,2),
        "budget" : round(budget,2),
        "budgetObject" : budgetObject,
        "excess" : round(excess,2),
        "under" : round(under,2),
        "reallocation" : round(reallocation,2),
    }

    return allocation

def SavingCreation(year, month):
    savingsCategory = AllocationCategory.objects.get(id=10)
    savingsAllocations = Allocation.objects.filter(category=savingsCategory).all()

    savings = []
    for allocation in savingsAllocations:
        monthStart = datetime.date(year,month,1)
        monthRange = monthrange(year, month)
        monthEnd = datetime.date(year,month, monthRange[1])

        query = TransactionAllocation.objects.filter(allocation=allocation)
        query = query.filter(transaction__date__range=["2000-01-01", monthEnd.strftime("%Y-%m-%d")]).all()
        query = query.aggregate(Sum('value'))
        value = query["value__sum"]
        if value is None:
            value = 0
        else:
            value = float(value)

        query = TransactionCapex.objects.filter(capex__paid_from=allocation)
        query = query.filter(transaction__date__range=["2000-01-01", monthEnd.strftime("%Y-%m-%d")]).all()
        query = query.aggregate(Sum('value'))
        valueCapex = query["value__sum"]
        if valueCapex is not None:
            value = value + float(valueCapex)

        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        valueStr = locale.currency(round(value,2), grouping=True)

        saving = {
            "allocation" : allocation,
            "value" : value,
            "valueStr" : valueStr,
            "month" : month,
            "year" : year,
        }

        savings.append(saving)

    return savings

# Summary
def Summary(request, year, month):
    startDate = datetime.date(year,month,1)
    endDate = startDate + relativedelta(months=1)
    endDate = endDate - relativedelta(days=1)

    weekBasisStart = FirstMonday(startDate)

    weekBasisEnd = weekBasisStart + relativedelta(weeks=4) + relativedelta(days=1)
    if weekBasisEnd.month == weekBasisStart.month:
        weekBasisEnd = weekBasisStart + relativedelta(weeks=5) - relativedelta(days=1)
    else: 
        weekBasisEnd = weekBasisStart + relativedelta(weeks=4) - relativedelta(days=1)

    allocations = []
    netTotal = 0
    allocationQuery = Allocation.objects.all()
    for a in allocationQuery:
        if a.category.name != "Reimbursable" and a.category.name != "Savings" and a.category.name != "Income":
            budgetObject = BudgetLock.objects.filter(year=year).filter(month=month).filter(allocation=a).first()

            dateStart = startDate
            dateEnd = endDate
            if budgetObject is not None:
                if budgetObject.basis == Budget.WEEK:
                    dateStart = weekBasisStart
                    dateEnd = weekBasisEnd

            # Credits
            query = TransactionAllocation.objects.filter(allocation=a)
            query = query.filter(transaction__type=Transaction.CREDIT)
            query = query.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")])
            query = query.aggregate(Sum('value'))
            credits = query["value__sum"]
            if credits is None:
                credits = 0
            else:
                credits = credits

            credits = float(credits)

            # Debits
            query = TransactionAllocation.objects.filter(allocation=a)
            query = query.filter(transaction__type=Transaction.DEBIT)
            query = query.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")])
            query = query.aggregate(Sum('value'))
            debits = query["value__sum"]
            if debits is None:
                debits = 0
            else:
                debits = -debits
                
            debits = float(debits)

            # Reallocations
            query = TransactionAllocation.objects.filter(allocation=a)
            query = query.filter(transaction__type=Transaction.EXCESS)
            query = query.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")])
            query = query.aggregate(Sum('value'))
            reallocation = query["value__sum"]
            if reallocation is None:
                reallocation = 0
            else:
                reallocation = -reallocation

            reallocation = float(reallocation)

            # Budget
            query = TransactionAllocation.objects.filter(allocation=a)
            query = query.filter(transaction__type=Transaction.BUDGET)
            query = query.filter(transaction__date__range=[dateStart.strftime("%Y-%m-%d"), dateEnd.strftime("%Y-%m-%d")])
            query = query.aggregate(Sum('value'))
            budget = query["value__sum"]
            if budget is None:
                budget = 0
            else:
                budget = budget

            budget = float(budget)

            # Balance
            balance = budget - reallocation - debits + credits
            balance = float(balance)

            # Net
            if balance < -0.1:
                net = budget - balance
            else:
                net = budget - reallocation
            net = float(net)

            netTotal += net

            allocation = {
                "object" : a,
                "credits" : round(credits,2),
                "debits" : round(debits,2),
                "reallocation" : round(reallocation,2),
                "budget" : round(budget,2),
                "balance" : round(balance,2),
                "net" : round(net,2),
            }

            allocations.append(allocation)

    context = {
        "allocations" : allocations,
        "netTotal" : netTotal,
    }

    return render(request, "summary.html", context)

# Transactions
def Transactions(request):
    transactions = Transaction.objects.all()
    transactions = transactions.exclude(type=Transaction.TRANSFER_DUPLICATE)

    transactionsCapex = Transaction.objects.all()

    if request.method == "POST":
        # Date Range
        startDate = request.POST.get('start_date', None)
        endDate = request.POST.get('end_date', None)
        if startDate is not None and endDate is not None:
            start = datetime.datetime.strptime(startDate, "%B %d, %Y")
            end = datetime.datetime.strptime(endDate, "%B %d, %Y")
        else:
            myDate = datetime.date.today()
            start = datetime.date(myDate.year,myDate.month,1)
            monthRange = monthrange(myDate.year, myDate.month)
            end = datetime.date(myDate.year,myDate.month, monthRange[1])

        transactions = transactions.filter(date__range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")]).all()
        transactionsCapex = transactionsCapex.filter(date__range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")]).all()

        # Allocation
        ids = request.POST.get('allocation_ids', None)
        allocation = None
        if ids is not None:
            list = ids.split()
            for id in list:
                allocation = Allocation.objects.filter(id=id).first()
                transactions = transactions.filter(allocations__allocation__id=id)
                transactionsCapex = transactionsCapex.filter(capex_allocation__capex__paid_from__id=id).distinct()

        # Allocation Exclusion
        ids = request.POST.get('allocation_ids_exclude', None)
        if ids is not None:
            list = ids.split()
            for id in list:
                transactions = transactions.exclude(allocations__allocation__id=id)

        # Category
        ids = request.POST.get('category_ids', None)
        if ids is not None:
            list = ids.split()
            for id in list:
                transactions = transactions.filter(allocations__allocation__category__id=id)

        # Category Exclusion
        ids = request.POST.get('category_ids_exclude', None)
        if ids is not None:
            list = ids.split()
            for id in list:
                transactions = transactions.exclude(allocations__allocation__category__id=id)

        # Types
        ids = request.POST.get('type_ids', None)
        if ids is not None:
            list = ids.split()
            for id in list:
                transactions = transactions.filter(type=id)

        # Types Exclusion
        ids = request.POST.get('type_ids_exclude', None)
        if ids is not None:
            list = ids.split()
            for id in list:
                transactions = transactions.exclude(type=id)

    else:
        myDate = datetime.date.today()
        start = datetime.date(myDate.year,myDate.month,1)
        monthRange = monthrange(myDate.year, myDate.month)
        end = datetime.date(myDate.year,myDate.month, monthRange[1])

        transactions = transactions.filter(date__range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")]).all()


    transactions= transactions.order_by("-date", "-value").all() 

    context = {
        "transactions" : transactions,
        "transactionsCapex" : transactionsCapex,
        "allocation" : allocation,
    }

    return render(request, "transactions.html", context)

# Budget
def BudgetView(request):
    budgetsQuery = Budget.objects.order_by("allocation__category__id","allocation__code").all()
    budgetsQuery = budgetsQuery.exclude(allocation__category__id=11).all() # exclude income
    budgetsQuery = budgetsQuery.exclude(allocation__category__id=10).all() # exclude savings
    budgetsQuery = budgetsQuery.exclude(allocation__category__id=9).all() # exclude reimbursable

    categoriesQuery = AllocationCategory.objects.all()
    categoriesQuery = categoriesQuery.exclude(id=11).all() # exclude income
    categoriesQuery = categoriesQuery.exclude(id=10).all() # exclude savings
    categoriesQuery = categoriesQuery.exclude(id=9).all() # exclude reimbursable

    incomeQuery = Budget.objects.filter(allocation__code="IN1").first()
    income = float(incomeQuery.value)

    budgets = []
    totalSpend = 0
    weekTotal = 0
    for budgetsQ in budgetsQuery:
        values = []

        valueWeek = 0
        valueFortnight = 0
        valueMonth = 0
        valueQuarter = 0
        valueYear = 0
        if budgetsQ.basis == 1:
            valueWeek = float(budgetsQ.value)
            valueFortnight = float(budgetsQ.value)*2
            valueMonth = float(budgetsQ.value)*4
            valueQuarter = float(budgetsQ.value)*12
            valueYear = float(budgetsQ.value)*48

            weekTotal += valueWeek 

        if budgetsQ.basis == 2:
            valueWeek = float(budgetsQ.value)/2
            valueFortnight = float(budgetsQ.value)
            valueMonth = float(budgetsQ.value)/8.6666
            valueQuarter = float(budgetsQ.value)*6.5
            valueYear = float(budgetsQ.value)*26
        if budgetsQ.basis == 3:
            valueWeek = float(budgetsQ.value)/4
            valueFortnight = float(budgetsQ.value)/8.6666
            valueMonth = float(budgetsQ.value)
            valueQuarter = float(budgetsQ.value)*3
            valueYear = float(budgetsQ.value)*12
        if budgetsQ.basis == 4:
            valueWeek = float(budgetsQ.value)/12
            valueFortnight = float(budgetsQ.value)/6.5
            valueMonth = float(budgetsQ.value)/3
            valueQuarter = float(budgetsQ.value)
            valueYear = float(budgetsQ.value)*4
        if budgetsQ.basis == 5:
            valueWeek = float(budgetsQ.value)/48
            valueFortnight = float(budgetsQ.value)/26
            valueMonth = float(budgetsQ.value)/12
            valueQuarter = float(budgetsQ.value)/4
            valueYear = float(budgetsQ.value)

        

        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        value = locale.currency(round(budgetsQ.value,2), grouping=True)

        values.append(locale.currency(round(valueWeek,2), grouping=True))
        values.append(locale.currency(round(valueFortnight,2), grouping=True))
        values.append(locale.currency(round(valueMonth,2), grouping=True))
        values.append(locale.currency(round(valueQuarter,2), grouping=True))
        values.append(locale.currency(round(valueYear,2), grouping=True))

        # Total Accumulation
        totalSpend += valueMonth

        # Count
        query = Budget.objects.filter(allocation__category=budgetsQ.allocation.category).all()
        query = query.aggregate(Count('value'))
        count = query["value__count"]

        budget = {
            "object" : budgetsQ,
            "values" : values,
            "valueWeek" : round(valueWeek,2),
            "valueMonth" : round(valueMonth,2),
            "allocation" : budgetsQ.allocation,
            "basis" : budgetsQ.basis,
            "value" : value,
            "account" : budgetsQ.account,
            "rollover" : budgetsQ.rollover,
            "excess_to_allocation" : budgetsQ.excess_to_allocation,
            'iterateover': range(5),
            "count" : count,
            "graphRows" : count+2,
        }

        budgets.append(budget)

    categories = []
    for categoryQ in categoriesQuery:
        budgetsQuery = Budget.objects.filter(allocation__category= categoryQ).all()

        value = 0

        for budgetsQ in budgetsQuery:
            if budgetsQ.basis == 1:
                value += float(budgetsQ.value)*4.3333
            if budgetsQ.basis == 2:
                value += float(budgetsQ.value)/8.6666
            if budgetsQ.basis == 3:
                value += float(budgetsQ.value)
            if budgetsQ.basis == 4:
                value += float(budgetsQ.value)/3
            if budgetsQ.basis == 5:
                value += float(budgetsQ.value)/12

        category = {
            "name" : categoryQ.name,
            "value" : value,
        }
        categories.append(category)

    # Weekly Reserve
    weeklyReserve = weekTotal/3

    totalSpend += weeklyReserve
    savings = income - totalSpend


    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
    income = locale.currency(round(income,2), grouping=True)    
    totalSpend = locale.currency(round(totalSpend,2), grouping=True)    
    savings = locale.currency(round(savings,2), grouping=True)
    weeklyReserve = locale.currency(round(weeklyReserve,2), grouping=True)

    context = {
        "budgets" : budgets,
        "categories" : categories,
        "income" : income,
        "totalSpend" : totalSpend,
        "savings" : savings,
        "weeklyReserve" : weeklyReserve,
    }

    return render(request, "budget.html", context)

# Unallocated
def Unallocated(request):
    transactions = Transaction.objects.exclude(type=Transaction.TRANSFER).all()
    transactions = transactions.exclude(type=Transaction.BUDGET).all()
    transactions = transactions.exclude(type=Transaction.TRANSFER_DUPLICATE).all()
    transactions = transactions.filter(allocations__isnull=True).all()
    transactions = transactions.filter(capex_allocation__isnull=True).all()
    transactions= transactions.order_by("-date").all()
    
    allocations = Allocation.objects.all()
    categories = AllocationCategory.objects.all()

    capexes = CapexApproval.objects.filter(status=CapexApproval.APPROVED).all()


    context = {
        "transactions" : transactions,
        "allocations" : allocations,
        "categories" : categories,
        "capexes" : capexes,
    }

    return render(request, "unallocated.html", context)

def SaveAllocations(request):
    data = json.loads(request.body.decode("utf-8"))
    errors=[]

    transactionAllocations = data['transactionAllocations']
    capitalAllocations = data['capitalAllocations']

    for transactionAllocation in transactionAllocations:
        transaction = Transaction.objects.filter(id=transactionAllocation['transaction']).first()
        allocation = Allocation.objects.filter(id=transactionAllocation['allocation']).first()

        if transaction.type == Transaction.DEBIT:
            value = -transaction.value
        else:
            value = transaction.value

        try:
            TransactionAllocation.objects.create(transaction=transaction, allocation=allocation, value=value)
            
        except:
            print("saving transaction failed: " + str(transaction))
            errors.append("Trouble saving transaction: " + str(transaction))

    for capitalAllocation in capitalAllocations:
        transaction = Transaction.objects.filter(id=capitalAllocation['transaction']).first()
        capex = Capex.objects.filter(id=capitalAllocation['allocation']).first()

        if transaction.type == Transaction.DEBIT:
            value = -transaction.value
        else:
            value = transaction.value

        try:
            TransactionCapex.objects.create(transaction=transaction, capex=capex, value=value)
        except:
            print("saving transaction failed: " + str(transaction))
            errors.append("Trouble saving transaction: " + str(transaction))

    
    response = {'errors':errors}

    return JsonResponse(response)

# Unallocated Transfers
def UnallocatedCreditsAll(request):
    transactions = Transaction.objects.filter(allocations__isnull=True).all()
    transactions = transactions.filter(capex_allocation__isnull=True).all()
    transactions = transactions.filter(Q(type=Transaction.CREDIT) | Q(type=Transaction.BUDGET, paid_from__isnull=True) | Q(type=Transaction.TRANSFER, paid_from__isnull=True)).all()

    allTransactions = Transaction.objects.exclude(type=Transaction.CREDIT).all()
    allTransactions = allTransactions.exclude(type=Transaction.TRANSFER).all()


    context = {
        "transactions" : transactions,
        "allTransactions" : allTransactions,
    }

    return render(request, "unallocated_credits.html", context) 

def UnallocatedCreditsToday(request):
    myDate = datetime.date.today()

    return redirect(reverse('unallocated_credits_date', kwargs={'year':myDate.year, 'month':myDate.month, 'day':myDate.day}))

def UnallocatedCredits(request, year, month, day):
    myDate = datetime.date(year,month,day)

    transactions = Transaction.objects.filter(allocation__isnull=True).all()
    transactions = transactions.filter(capex_allocation__isnull=True).all()
    transactions = transactions.filter(date__year=str(myDate.year)).all()
    transactions = transactions.filter(date__month=str(myDate.month)).all()
    transactions = transactions.filter(date__day=str(myDate.day)).all()
    transactions = transactions.filter(Q(type=Transaction.CREDIT) | Q(type=Transaction.BUDGET) | Q(type=Transaction.TRANSFER, paid_from__isnull=True)).all()

    allTransactions = Transaction.objects.filter(date__year=str(myDate.year)).all()
    allTransactions = allTransactions.filter(date__month=str(myDate.month)).all()
    allTransactions = allTransactions.filter(date__day=str(myDate.day)).all()
    allTransactions = allTransactions.exclude(type=Transaction.CREDIT).all()


    context = {
        "transactions" : transactions,
        "allTransactions" : allTransactions,
    }

    return render(request, "unallocated_credits.html", context)    

def SaveTransfers(request):
    data = json.loads(request.body.decode("utf-8"))
    errors=[]

    transfers = data['transfers']

    for transfer in transfers:
        paidToTransaction = Transaction.objects.filter(id=transfer['paid_to']).first()
        paidFromTransaction = Transaction.objects.filter(id=transfer['paid_from']).first()

        try:
            paidToTransaction.paid_from = paidFromTransaction.paid_from
            if transfer["reserve"] == True:
                paidToTransaction.type = Transaction.BUDGET
            else:
                paidToTransaction.type = Transaction.TRANSFER
            paidToTransaction.save()

            try:
                paidFromTransaction.paid_to = paidToTransaction.paid_to
                paidFromTransaction.type = Transaction.TRANSFER_DUPLICATE
                paidFromTransaction.save()
            except:
                print("saving transaction failed: " + str(paidFromTransaction))
                errors.append("Trouble saving transaction: " + str(paidFromTransaction))

        except:
            print("saving transaction failed: " + str(paidToTransaction))
            errors.append("Trouble saving transaction: " + str(paidToTransaction))


        
    
    response = {'errors':errors}

    return JsonResponse(response)

def CapexView(request):
    capexs = Capex.objects.exclude(status__status=CapexApproval.CLOSED).all()
    capexs = capexs.annotate(total=Sum(F('items__price')*F('items__qty')))
    capexs = capexs.annotate(first_date=Min('items__dateEstimate'))
    capexs = capexs.order_by("first_date","status__status", "status__approved_by")

    myDate = datetime.datetime.today()

    months = []
    for i in range(5):
        thisDate = myDate + relativedelta(months=i)
        name = thisDate.strftime("%B")

        capexItems = CapexItems.objects.exclude(capex__status__status=CapexApproval.DRAFT).all()

    context = {
        "capexs" : capexs,
    }

    return render(request, "capex.html", context)






