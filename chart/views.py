from django.shortcuts import render
from pprint import pprint as pp
from .models import Order
import json
from django.db.models import Sum
# Create your views here.

def index(request):
    orders = Order.objects.values('price_ruble', 'delivery_time').order_by('id')
    delivery_dates = [order['delivery_time'] for order in orders]
    price_ruble = [order['price_ruble'] for order in orders]
    total_price = orders.aggregate(Sum('price_ruble'))
    context = {
        'delivery_dates' : json.dumps(delivery_dates),
        'price_ruble' : json.dumps(price_ruble),
        'total_price': round(total_price['price_ruble__sum'], 3)
    }
    return render(request, 'chart/chart.html', context)