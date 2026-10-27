from django.urls import path
from . import views

urlpatterns = [
    path('', views.core, name='core'),
    path('core/', views.core, name='core'),
    path("insert-user/", views.insert_user, name="insert_user"),
    path("insert-course/", views.insert_course, name="insert_course"),

    path('statistik/', views.statistik, name='statistik'),
    path('statistik-api/', views.statistik_from_api, name='statistik_api'),
    path('course-stat/', views.courseStat, name='course_stat'),
    path('user-stats/', views.userStatistics, name='userStatistics'),
    path("users/", views.user_list, name="user_list"),
    path("users/json/", views.user_json, name="user_json"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("search-user/", views.search_user, name="search_user"),

    path("update-user/<int:pk>/", views.update_user, name="update_user"),
    path("delete-user/<int:pk>/", views.delete_user, name="delete_user"),
    path("delete-courses/", views.delete_all_courses, name="delete_all_courses"),
    path(
        "delete-users-except/<int:pk>/",
        views.delete_users_except,
        name="delete_users_except",
    ),
]