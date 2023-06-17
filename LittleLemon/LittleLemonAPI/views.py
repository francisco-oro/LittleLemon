from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from .models import *
from django.contrib.auth.models import User, UserManager
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.contrib.auth import get_user_model

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
            return Response({'message':'ok'}, status.HTTP_201_CREATED)
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
    managers = Group.objets.get(name='Manager')
    user.is_staff=False 
    managers.user_set.remove(user)
    user.save()
    return Response({'message':'ok'}, status.HTTP_200_OK)

@api_view(['GET','POST'])
@permission_classes([IsAdminUser])
def ViewCreateDeliveryUser(request):
    username = request.data['username']
    if username:
        if request.method == 'POST':
            user = get_object_or_404(User, username=username)
            delivery_staff = Group.objects.get(name='Delivery')
            delivery_staff.user_set.add(user)
            return Response({'message':'ok'}, status.HTTP_201_CREATED)
        if request.method == 'GET':
            managers = user_model.objects.filter(is_staff=True).all()
            serializer = SuperuserSerializer(managers, many=True)
            return Response(serializer.data)
        
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def RemoveDeliveryUser(request, pk):
    user = get_object_or_404(User, id=pk)
    delivery_staff = Group.objects.get(name='Delivery')
    delivery_staff.user_set.remove(user)
    user.save()
    return Response({'message':'ok'}, status.HTTP_200_OK)


##################################
# Cart management endpoints 
##################################
class ListCreateDeleteCartItems(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()

# @api_view(['GET','POST','DELETE'])
# @permission_classes([IsAuthenticated])
# def ListCreateDeleteCartItems(request):
#     # Only Customers can edit, view and add items to their cars
#     username = request.username
#     if username:
#         is_staff = User.objects.filter(
#             username=username,
#             groups__name__in=['Delivery']
#         ).exists()
#         if(is_staff):
#             return Response({'message':'Reserved for customers'}, status.HTTP_401_UNAUTHORIZED)
#         if request.method == 'GET':
#             user = get_object_or_404(User, username=username)
#             menu_items = Cart.objects.get(user = user.pk)
#             serializer = CartSerializer(menu_items, many=True)
#             return Response(serializer.data)
#         if request.method == 'POST':
#             pass
        

##################################
# Order Management Endpoints 
##################################
def ListCreateOrders(request):
    username = request.username
    is_manager = User.objects.filter(username=username, groups__name__int=['Manager'])
    is_delivery = User.objects.filter(username=username, groups__name__int=['Delivery'])
    user = get_object_or_404(User, username=username)
    # Manager permissions: View
    if is_manager:
        if request.method == 'GET':
            orders = Order.objects.all()
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)
    # Delivery permissions: View orders assigned to them
    elif is_delivery: 
        if request.method == 'GET':
            orders = Order.objects.get(delivery_crew=user.pk)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)
    # Client permissions: View and edit their own orders
    else:
        if request.method == 'GET':
            orders = Order.objects.get(user = user.pk)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)
        if request.method == 'POST':
            orders = Cart.objects.get(user = user.pk)
            serializer = OrderSerializer(data = orders, many=True)
            if serializer.is_valid():
                serializer.save(user=user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)