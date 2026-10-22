

from django.contrib import admin
from django.urls import path
from onlinecourse import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path(
        'course/<int:course_id>/',
        views.course_details,
        name='course_details'
    ),
    path(
        'course/<int:course_id>/exam/',
        views.exam,
        name='exam'
    ),
    path(
        'course/<int:course_id>/submit/',
        views.submit,
        name='submit'
    ),
    path(
        'exam/result/<int:submission_id>/',
        views.show_exam_result,
        name='show_exam_result'
    ),
]


