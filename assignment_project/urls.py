from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import path

from django.conf import settings
from django.views.static import serve

from . import views

urlpatterns = [
                  path('', views.main, name='main_page'),
                  path('assignments', views.assignment, name='as'),
                  path(r'qstn/<int:aid>/qstn', views.qstn, name='qstn'),
                  path('stu_register', views.register, name='stu_register'),
                  path('stu_login', views.stu_login, name='stu_login'),
                  path('teacher', views.teacher, name='teacher'),
                  path('qstnv/<int:aid>/qstnv', views.qstn_view, name='qstnv'),
                  path('new_assignment', views.new_as, name='new_as'),
                  path('add_qstn', views.add_qstn, name='add_qstn'),
                  path('delo/<int:xoy>/<int:aorq>', views.delo, name='delo'),
                  path('del_as', views.del_as, name='del_as'),
                  path('del_qstn', views.del_qstn, name='del_qstn'),
                  path('edit_q/<int:pk>', views.edit_q, name='edit_q'),
                  path('qstnv/<int:aid>', views.qstn_view, name='qsntv'),
                  path('results', views.results, name='results'),
                  path('my_assignments', views.mas, name='my_assignments'),
                  path('view_results', views.vresults, name='view_results'),
                  path('view_r/<str:spk>', views.viewr, name='view_r'),
                  path('edit_as', views.edit_as, name='edit_as'),
                  url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
                  url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
              ] + static(settings.STATIC_URL, doucument_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL,
                      document_root=settings.MEDIA_ROOT)
