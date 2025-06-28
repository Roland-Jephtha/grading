from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static






# admin.site.site_header = "My Company Administration"
# admin.site.site_title = "My Company Admin Portal"
# admin.site.index_title = "Welcome to My Company Administration"



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('grading.urls'))
]




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
