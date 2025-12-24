from django.contrib import admin
from django.urls import path, include

urlpatterns = [
	path('admin/', admin.site.urls),
	path('api/auth/', include('authentication.urls')),
	path('api/core/', include('core.urls')),
	path('api/accounts/', include('accounts.urls')),
	path('api/dimensions/', include('dimensions.urls')),
	path('api/financials/', include('financials.urls')),
	path('api/data_ingestion/', include('data_ingestion.urls')),
	path('api/reports/', include('reports.urls')),
]
