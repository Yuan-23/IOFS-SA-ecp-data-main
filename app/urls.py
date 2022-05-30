from django.contrib import admin
from django.urls import path
from . import views, test2db

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stu_detail/<student_id>/', views.stu_detail),
    path('stu_detail1/<student_id>/', views.stu_detail1),
    path('stu_detail2/', views.stu_detail2)
]