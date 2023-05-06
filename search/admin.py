from django.contrib import admin
from .models import *

# Register your models here.
class CourseInLine(admin.TabularInline):
    model = Course
    extra = 1

class DepartmentAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Full Name", {"fields": ["name"]}),
        ("Abbreviated", {"fields": ["short_name"]})
    ]
    inlines = [CourseInLine]
    list_display = ["name", "short_name"]
    list_filter = ["name"]
    search_fields = ["name", "short_name"]

class TermAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["osu_id"]}),
        ("Term Information", {"fields": ["name"]})
    ]

class InstructorAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Department", {"fields": ["department"]}),
        ("Name", {"fields": ["first_name", "last_name"]})
    ]

class Course_SectionAdmin(admin.ModelAdmin):
    fieldsets = [

    ]


admin.site.register(Term, TermAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Course_Section, Course_SectionAdmin)