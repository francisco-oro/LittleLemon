from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('menu-items', views.ViewCreateMenuItems.as_view(), name='view_menu_items'),
    path('menu-items/<int:pk>',views.SingleMenuItemView.as_view()),
    path('groups/manager/users',views.ViewCreateManager),
    path('groups/manager/users/<int:pk>', views.RemoveFromManagers),
    path('groups/delivery-crew/users',views.ViewCreateDeliveryUser),
    path('groups/delivery-crew/users/<int:pk>', views.RemoveDeliveryUser),
    path('cart/menu-items', views.ViewAddDeleteCartItems,name='cart_items'),
    path('orders', views.ListCreateOrders),
    path('orders/<int:pk>', views.DeleteUpdateView),
    path('generator/user', views.generate_random_user),
]