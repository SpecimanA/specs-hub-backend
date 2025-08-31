# reporting/views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from sales.models import Opportunity
from django.db.models import Sum, F
from django.db.models.functions import ExtractMonth, ExtractYear
from collections import defaultdict
import calendar

@staff_member_required
def financial_report_view(request):
    # --- Data Aggregation Logic ---
    opportunities = Opportunity.objects.filter(close_date__year=2025)

    # Forecasted revenue and profit, weighted by probability
    forecast = opportunities.annotate(
        year=ExtractYear('close_date'),
        month=ExtractMonth('close_date')
    ).values('year', 'month').annotate(
        forecasted_revenue=Sum(F('amount') * F('stage__win_probability')),
        forecasted_profit=Sum(F('total_profit') * F('stage__win_probability'))
    ).order_by('year', 'month')

    # Prepare data for template
    report_data = defaultdict(lambda: {'revenue': 0, 'profit': 0})
    for item in forecast:
        month_name = calendar.month_abbr[item['month']]
        report_data[month_name]['revenue'] = round(item['forecasted_revenue'], 2)
        report_data[month_name]['profit'] = round(item['forecasted_profit'], 2)

    context = {
        'title': 'Financial Forecast Report 2025',
        'report_data': dict(report_data),
    }
    return render(request, 'admin/financial_report.html', context)