from django.contrib import admin
from .models import User, Course, CourseMember, CourseContent,Comment
# Register your models here.
admin.site.register(CourseMember)
admin.site.register(Course)
admin.site.register(CourseContent)
admin.site.register(Comment)