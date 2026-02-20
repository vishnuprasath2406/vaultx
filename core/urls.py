from django.urls import path
from . import views

urlpatterns = [

    # LOGIN
    path('', views.login_view, name="login"),
    path('verify-otp/', views.verify_otp, name="verify_otp"),
    path('logout/', views.logout_view, name="logout"),

    # DASHBOARDS
    path('customer/', views.customer, name="customer"),
    path('seller/', views.seller, name="seller"),
    path('service/', views.service, name="service"),

    # PRODUCT
    path('add-product/', views.add_product, name="add_product"),
    path('dashboard-stats/', views.dashboard_stats, name="dashboard_stats"),

    # CLAIMS (HTML)
    path('raise-claim/', views.raise_claim, name="raise_claim"),

    # CLAIM API (AJAX)
    path('service-claims-data/', views.service_claims_data, name="service_claims_data"),
    path('service-update-claim/', views.service_update_claim, name="service_update_claim"),

    # CUSTOMER APIs
    path("search-customer-api/", views.search_customer_api),
    path("customer-claims-api/", views.customer_claims_api),
    path("customer-dashboard-api/", views.customer_dashboard_api),
    path("raise-claim-api/", views.raise_claim_api),

    # CHATBOT
    path("chatbot_api/", views.chatbot_api, name="chatbot_api"),

    # SEARCH
    path("search-customer/<str:cid>/", views.search_customer),
    path("service-dashboard-api/", views.service_dashboard_api),

]
