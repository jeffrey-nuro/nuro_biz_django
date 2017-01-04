from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^route$', views.route, name='route'),
    url(r'^reachable_region$', views.reachable_region, name='reachable_region'),
    url(r'^simulate$', views.simulate, name='simulate'),
    url(r'^.*$', views.index, name='index'),
]
