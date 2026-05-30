"""MoneyManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import schema as _schema  # noqa: F401  # register OpenAPI auth extension

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-admin/", include("users.admin_api_urls")),
    path("user/", include("users.urls")),
    path("accounts/", include("account.urls")),
    path("transactions/", include("transaction.urls")),
    path("bank-statements/", include("bankstatements.urls")),
    path("reports/", include("reports.urls")),
    path("budgets/", include("budgets.urls")),
    path("recurring-transactions/", include("recurring.urls")),
    path("alerts/", include("alerts.urls")),
]

if settings.API_DOCS_ENABLED:
    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]
