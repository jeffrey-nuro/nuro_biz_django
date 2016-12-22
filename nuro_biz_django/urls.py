from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^business_dashboard/', include('business_dashboard.urls')),
    url(r'^admin/', admin.site.urls),
]
