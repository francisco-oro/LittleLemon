from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import Group, User
from django.contrib.auth import get_user_model
from django.db.models import Sum
import datetime

User_model = get_user_model()
# Get the delivery group 
delivery_group = Group.objects.get(name='Delivery')

# Users that belong to the delivery group 
delivery_users = User.objects.filter(groups=delivery_group)

class MenuItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'

class SuperuserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_model
        fields = ['username','email']
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_model
        fields = ['username', 'email']


class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default = serializers.CurrentUserDefault()
    )
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset = MenuItem.objects.all()
    )
    quantity = serializers.DecimalField(max_digits=6, decimal_places=2)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem','quantity','unit_price','price']
    def create(self, validated_data):
        return Cart.objects.create(**validated_data)
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity',instance.quantity)
  

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default= serializers.CurrentUserDefault()
    )
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset = delivery_users
    )
    status = serializers.BooleanField(default=False)
    date = serializers.DateField(default = datetime.datetime.now())
    total = serializers.DecimalField(max_digits=6, decimal_places=2)
    order_items = serializers.SerializerMethodField(method_name='get_order_names')

    def get_order_items(self,order):
        order_items = OrderItem.objects.filter(order=order)
        order_items_serializer = OrderItemSerializer(order_items, many=True)
        return order_items_serializer.data

    class Meta:
        model=Order
        fields=['id','user','delivery_crew','status','date','total', 'order_items']
    


class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all()
    )
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all()
    )
    quantity = serializers.DecimalField(max_digits=6, decimal_places=2)
    class Meta:
        model = OrderItem
        fields = '__all__'