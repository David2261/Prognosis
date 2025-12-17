from django.contrib import admin
from django.urls import path, include

urlpatterns = [
	path('admin/', admin.site.urls),
	path('api/auth/', include('apps.authentication.urls')),
	path('api/core/', include('apps.core.urls')),
	path('api/accounts/', include('apps.accounts.urls')),
	path('api/dimensions/', include('apps.dimensions.urls')),
]
