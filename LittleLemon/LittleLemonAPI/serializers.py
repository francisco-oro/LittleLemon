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
    # Inputs allowed from the user : menuitem and quantity
    # There's already a unique_together description declared in the Cart model 
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        default = serializers.CurrentUserDefault()
    )
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all()
    )
    quantity = serializers.DecimalField(max_digits=6, decimal_places=2)
    # Calculate the total price for the current item instance
    price = serializers.SerializerMethodField(method_name= 'calculate_price')
    unit_price = serializers.SerializerMethodField(method_name='get_unit_price')

    # Calculate the total price
    def calculate_price(self):
        return self.quantity * self.menuitem.price
    # Return the price per items bought
    def get_unit_price(self):
        return self.menuitem.price

    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'quantity', 'unit_price', 'price']
        # Limit the input accepted by quantity
        extra_kwargs = {
            'quantity' : {
                'min_value': 1,
                'max_value': 100,
            }
        }


class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all()
    )
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all()
    )
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2)
    quantity = serializers.DecimalField(max_digits=6, decimal_places=2)
    price = serializers.SerializerMethodField(method_name='calculate_price')
    def calculate_price(self, product:OrderItem):
        return product.unit_price * product.quantity
    class Meta:
        model = OrderItem
        fields = '__all__'
    

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
    quantity = serializers.DecimalField(max_digits=6, decimal_places=2)
    orders = OrderItemSerializer
    class Meta:
        model=Order
        fields=['user','delivery_crew','status','date','quantity','orders']