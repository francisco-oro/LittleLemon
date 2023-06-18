from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from .models import *
from django.contrib.auth.models import User, UserManager
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import secrets
import string
import json

# Models and global variables
user_model = get_user_model()
delivery_group = Group.objects.get(name='Delivery')
manager_group = Group.objects.get(name='Manager')

delivery_users = User.objects.filter(groups=delivery_group)
manager_users = User.objects.filter(groups=manager_group)

class ViewCreateMenuItems(generics.ListCreateAPIView):
    queryset =  MenuItem.objects.all()
    serializer_class = MenuItemsSerializer
    def get_permissions(self):
        if(self.request.method=='GET'):
            return[]
        return[IsAdminUser()]
    
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset =  MenuItem.objects.all()
    serializer_class = MenuItemsSerializer
    def get_permissions(self):
        if(self.request.method=='GET'):
            return[]
        return[IsAdminUser()]

##################################
# User group management endpoints
##################################
@api_view(['POST','GET'])
@permission_classes([IsAdminUser])
def ViewCreateManager(request):
    # Add a new user to the Manager Group 
    if request.method == 'POST':
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)
            user.is_staff=True
            user.save()
            return Response({'id': user.pk, 'username':user.username,'email':user.email}, status.HTTP_201_CREATED)
        return Response({'message':'error'}, status.HTTP_404_NOT_FOUND)
    # Retrieve all the superusers
    if request.method == 'GET':
        managers = user_model.objects.filter(is_staff=True).all()
        serializer = SuperuserSerializer(managers, many=True)
        return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def RemoveFromManagers(request, pk):
    user = get_object_or_404(User, id=pk)
    managers = Group.objects.get(name='Manager')
    user.is_staff=False 
    managers.user_set.remove(user)
    user.save()
    return Response({'message':'success'}, status.HTTP_200_OK)

@api_view(['GET','POST'])
@permission_classes([IsAdminUser])
def ViewCreateDeliveryUser(request):
    username = request.data['username']
    if username:
        if request.method == 'POST':
            user = get_object_or_404(User, username=username)
            delivery_staff = Group.objects.get(name='Delivery')
            delivery_staff.user_set.add(user)
            user.save()
            return Response({'id': user.pk, 'username':user.username,'email':user.email}, status.HTTP_201_CREATED)
        if request.method == 'GET':
            serializer = SuperuserSerializer(delivery_users, many=True)
            return Response(serializer.data)
        
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def RemoveDeliveryUser(request, pk):
    user = get_object_or_404(User, id=pk)
    delivery_staff = Group.objects.get(name='Delivery')
    delivery_staff.user_set.remove(user)
    delivery_staff.save()
    return Response({'message':'ok'}, status.HTTP_200_OK)


##################################
# Cart management endpoints 
##################################

@api_view(['GET','POST','DELETE'])
@permission_classes([IsAuthenticated])
def ViewAddDeleteCartItems(request):
    user = request.user
    if request.method == 'GET':
        cart_items = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)
    if request.method == 'POST':
        # Retrieve the unit price from the Menu Items
        menu_item = get_object_or_404(MenuItem, pk=int(request.data.get('menuitem')))
        quantity = int(request.data.get('quantity'))
        data = {
            'user': user.id,
            'menuitem': menu_item.pk,
            'quantity': quantity,
            'unit_price': menu_item.price,
            'price': quantity * menu_item.price
        }
        serializer = CartSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    if request.method == 'DELETE':
        cart_items = Cart.objects.filter(user=user)
        cart_items.delete()
        return Response({'message':'success'}, status.HTTP_200_OK)
##################################
# Order Management Endpoints 
##################################

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
# Multiple Orders 
def ListCreateOrders(request):
    user = request.user
    is_manager = User.objects.filter(pk=user.id, groups=manager_group)
    is_delivery = User.objects.filter(pk=user.id, groups=delivery_group)
    # Manager permissions: View
    if is_manager:
        if request.method == 'GET':
            # Retrieve all the orders
            orders = Order.objects.all()
            orders_serializer = OrderSerializer(orders, many=True)
            
            # Select all the order items with related orders
            order_items = OrderItem.objects.select_related('order').all()
            order_items_serializer = OrderItemSerializer(order_items, many=True)
            

            # Arrange the elemetnts neatly
            for order in orders_serializer.data:
                for order_item in order_items_serializer.data:
                    if order['id'] == order_item['order']:
                        if 'menu-items' not in order.keys():
                            order['menu-items'] = [order_item]
                        else:
                            order['menu-items'].append(order_item)
            
            return Response(orders_serializer.data, status.HTTP_200_OK)
    # Delivery permissions: View orders assigned to them that haven't been delivered
    elif is_delivery: 
        if request.method == 'GET':
            # Retrieve all the orders assigned to the current delivery user
            orders = Order.objects.filter(delivery_crew=user, status=False)
            orders_serializer = OrderSerializer(orders, many=True)
            # Retrieve each order's unique primary key 
            orders_keys = [order['id'] for order in orders_serializer.data]
            # Retrieve all the order items with such orders
            order_items = OrderItem.objects.select_related('order').filter(order__in = orders_keys)
            order_items_serializer = OrderItemSerializer(order_items, many=True)

            # Arrange the elements neatly
            for order in orders_serializer.data:
                for order_item in order_items_serializer.data:
                    if order['id'] == order_item['order']:
                        if 'menu-items' not in order.keys():
                            order['menu-items'] = [order_item]
                        else:
                            order['menu-items'].append(order_item)
            
            return Response(orders_serializer.data, status.HTTP_200_OK)
    # Client permissions: View and edit their own orders
    else:
        if request.method == 'GET':
            # Retrieve all the orders created by the user
            orders = Order.objects.filter(user=user)
            order_serializer = OrderSerializer(orders, many=True)

            # Retrieve order items for each order
            order_items = OrderItem.objects.filter(order__in=orders)
            order_items_serializer = OrderItemSerializer(order_items, many=True)
            
            # Combine orders and order items in the response
            data = {
                'orders':order_serializer.data,
                'items':order_items_serializer.data
            }

            return Response(data, status.HTTP_200_OK)
        if request.method == 'POST':
            # Retrieve current cart items for the user
            cart_items = Cart.objects.filter(user=user)

            # Create a new order for the user.
            # Calculate the total based on cart items
            total = sum(cart_item.price for cart_item in cart_items)
            order = Order.objects.create(user=user, total=total, date=datetime.datetime.now())
            # Create order items from cart items
            order_items = []
            # Create a variable to store the total price for all
            # the items in that order
            total_price = 0
            for cart_item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    menuitem=cart_item.menuitem,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    price=cart_item.price
                )
                total_price += cart_item.price
                order_items.append(order_item)


            # Delete all items from the cart for the user
            cart_items.delete()

            # Serialize the order items
            order_items_serializer = OrderItemSerializer(order_items, many=True)
            return Response(order_items_serializer.data, status=201)
            
# A specific order
@api_view(['GET','PUT','PATCH','DELETE'])
@permission_classes([IsAuthenticated])

def DeleteUpdateView(request, pk):
    user = request.user
    is_manager = User.objects.filter(pk=user.id, groups=delivery_group)
    is_delivery = User.objects.filter(pk=user.id, groups=manager_group)
    user = get_object_or_404(User, id=user.id)
    order = get_object_or_404(Order, pk=pk)
    # Manager permissions: Delete order, get all orders, assign a crew
    # member to a specific order
    if is_manager:
        if request.method == 'PUT':
            # Check if the delivery staff ID is provided in the
            # request body
            delivery_staff_id = request.data.get('delivery_crew')
            if delivery_staff_id is not None:
                # Retrieve the delivery staff user order 
                delivery_staff = get_object_or_404(User, p=delivery_staff_id)
                
                # Assign the delivery staff for the order
                order.delivey_crew = delivery_staff
                order.save()

                serializer = OrderSerializer(order)
                return Response(serializer.data)
        # Update the order status: (0) for out of delivery (1) for delivered
        if request.method == 'PATCH':
            order.status = request.data.get('status')
            order.save()
            serializer = OrderSerializer(order)
            return Response(serializer.data)
                # Remove the order from the server
        if request.method == 'DELETE': 
            order.delete()
            return Response({'message':'record deleted'}, status.HTTP_200_OK)
        return Response(status.HTTP_405_METHOD_NOT_ALLOWED)

    if is_delivery:
        if request.method == 'PATCH':
            order.status = request.data.get('status')
            order.save()
            return Response({'message':'Succesfully updated'}, status.HTTP_202_ACCEPTED)
         
    # Customer permissions: view and update their orders
    else: 
        if request.method == 'GET':
            if user == order.user:
                serializer = OrderSerializer(order)
                return Response(serializer.data)
    return Response({'message':'Not allowed to view this item'}, status.HTTP_401_UNAUTHORIZED)

##################################
# Utilities
##################################

@api_view(['GET'])
def generate_random_user(request, domain='littlelemon.com'):
    username_chars = string.ascii_lowercase + string.digits
    password_chars = string.ascii_letters + string.digits + string.punctuation
    random_username = ''.join(secrets.choice(username_chars) for i in range(8))
    random_password = ''.join(secrets.choice(password_chars) for i in range(12))
    random_email = f'{random_username}@{domain}'
    return Response({'username':random_username, 
                     'password':random_password,
                     'email':random_email})