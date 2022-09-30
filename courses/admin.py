from django.contrib import admin

# Register your models here.
from .models import Department, Course, Module

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
class ModuleInline(admin.StackedInline):
    model = Module
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'created']
    list_filter = ['created', 'department']
    search_fields = ['title', 'overview']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
