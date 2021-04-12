from django.contrib import admin
from .models import UserProfile, Assignment, Question, Choice, GradedAssignment, Completed


admin.site.register(UserProfile)
admin.site.register(Assignment)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(GradedAssignment)
admin.site.register(Completed)