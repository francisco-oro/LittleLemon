from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('menu-items', views.ViewCreateMenuItems.as_view(), name='view_menu_items'),
    path('menu-items/<int:pk>',views.SingleMenuItemView.as_view()),
    path('groups/manager/users',views.ViewCreateManager),
]