
from django.urls import path
from .views import vila_list
urlpatterns = [
    path('list/', vila_list.as_view(), name='list_vila_home'),
]  
