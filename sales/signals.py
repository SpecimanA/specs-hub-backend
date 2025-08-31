# sales/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OpportunityProduct, Opportunity
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from decimal import Decimal

@receiver([post_save, post_delete], sender=OpportunityProduct)
def update_opportunity_totals(sender, instance, **kwargs):
    """
    This signal automatically recalculates the totals for an Opportunity
    whenever a related OpportunityProduct is saved or deleted.
    """
    opportunity = instance.opportunity
    
    aggregates = opportunity.opportunityproduct_set.aggregate(
            total_amount=Coalesce(Sum('line_total'), Value(Decimal('0.0'))),
            total_cost=Coalesce(Sum(F('quantity') * F('product__purchase_price')), Value(Decimal('0.0'))),
            total_agent_fee=Coalesce(Sum(F('line_total') * (F('agent_percentage') / Decimal('100.0'))), Value(Decimal('0.0')))
        )

    total_amount = aggregates['total_amount']
    total_cost = aggregates['total_cost']
    total_agent_fee = aggregates['total_agent_fee']

    opportunity.amount = total_amount
    opportunity.total_costs = total_cost
    opportunity.total_agent_fee = total_agent_fee
    opportunity.total_profit = total_amount - total_cost - total_agent_fee
    
    if total_amount > 0:
        opportunity.profit_percentage = float(opportunity.total_profit / total_amount) * 100
    else:
        opportunity.profit_percentage = 0.0

    # Use update() to save the fields and avoid recursion
    Opportunity.objects.filter(pk=opportunity.pk).update(
        amount=opportunity.amount,
        total_costs=opportunity.total_costs,
        total_agent_fee=opportunity.total_agent_fee,
        total_profit=opportunity.total_profit,
        profit_percentage=opportunity.profit_percentage
    )
