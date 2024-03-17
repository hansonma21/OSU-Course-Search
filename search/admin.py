from django.contrib import admin
from django_q import models as q_models
from django_q import admin as q_admin
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
        ("Term Information", {"fields": ["name"]}),
        ("Display", {"fields": ["display_boolean"]})
    ]
    list_display = ["name", "osu_id", "display_boolean"]
    list_filter = ["name"]
    search_fields = ["name"]

class CourseAdmin(admin.ModelAdmin):
    fieldsets = [

    ]

    list_filter = ["department", "number"]
    list_display = ["department", "number", "name"]
    search_fields = ["department__short_name", "number", "name"]


class InstructorAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Department", {"fields": ["department"]}),
        ("Name", {"fields": ["first_name", "last_name"]})
    ]

    list_filter = ["department", "first_name", "last_name"]
    list_display = ["first_name", "last_name", "department"]

    search_fields = ["department__short_name", "first_name", "last_name", "id"]


class Course_SectionAdmin(admin.ModelAdmin):
    raw_id_fields = ["instructors"]
    fieldsets = [
        ("Instructors", {"fields": ["instructors"]}),
        ("Section Information", {"fields": ["section_info", "days_and_times", "start_date", "end_date", "room", "availability"]}),
        ("Barret Data", {"fields": ["barrett_data_json"]}),
    ]

    list_display = ["course", "term", "section_id", "link_number", "availability", "barrett_data_json"]

    search_fields = ["section_id", "course__department__short_name", "course__number", "term__name", "instructors__last_name"]


class Search_QueryAdmin(admin.ModelAdmin):
    fieldsets = [

    ]

    list_display = ["search_query", "timestamp"]
    search_fields = ["search_query__term", "search_query__subject", "search_query__number", "search_query__instructor"]


class Error_LogAdmin(admin.ModelAdmin):
    fieldsets = [

    ]

    list_display = ["function_name", "error_message", "timestamp"]
    list_filter = ["function_name"]

class ScheduleAdmin(q_admin.ScheduleAdmin):
    fieldsets = [

    ]


admin.site.register(Term, TermAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Course_Section, Course_SectionAdmin)
admin.site.register(Search_Query, Search_QueryAdmin)
admin.site.register(Error_Log, Error_LogAdmin)
# admin.site.register(q_models., BruhAdmin)
# admin.site.register()