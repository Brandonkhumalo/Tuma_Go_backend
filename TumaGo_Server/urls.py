from django.urls import path

from TumaGo import settings
from django.conf.urls.static import static
from .views.UserViews import views, userViews
from .views.DriverViews import authViews, driverViews

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('update/user/profile/', views.update_profile, name='update_profile'),
    path('user/Data/', userViews.GetUserData, name='User_Data'),
    path('sync/time/', views.sync_time, name='Sync_Time'),
    path('trip_Expense/', userViews.GetTripExpenses, name='Trip_Expense'),
    path('cancel/delivery/', userViews.cancel_delivery, name='cancel_delivery'),
    path('rate/driver/', userViews.rate_driver, name='rate_driver'),

    path('login/', views.login, name='login'),
    path('verify_token/', views.VerifyToken, name='VerifyToken'),
    path('logout/', views.logout, name='logout'),
    path('delete/account/', authViews.delete_account, name='delete_account'),
    path('delivery/request/', driverViews.RequestDelivery, name='Delivery_Request'),
    path('reset_password/', authViews.change_password, name='change_password'), #Both apps
    path('get/deliveries/', driverViews.get_deliveries, name='get_user_or_driver_deliveries'),
    path('verifyTerms/', views.check_terms, name='Check_User_Terms'),
    path('accept/terms/', views.accept_terms, name='Accept_terms'),

    #all users
    path('allUsers/', views.get_all_users, name='All_Users'),
    path('allDeliveries/', views.get_all_deliveries, name='All_deliveries'),
    path('delete/', views.delete_all_users, name='All_Users'),

    #Driver
    path('driver/signup/', authViews.driver_register, name='driver_signup'),
    path('driver/data/', driverViews.get_driver_data, name='driver_data'),
    path('save-fcm-token/', authViews.save_fcm_token, name='save_fcm_token'),
    path('driver/offline/', authViews.driver_offline, name='driver_offline'),
    path('add/vehicle/', authViews.driver_vehicle, name='add_driver_vehicle'),
    path('accept/trip/', driverViews.AcceptTrip, name="Accept_trip"),
    path('end_trip/', driverViews.end_trip, name='end_trip'),
    path('add/license/', authViews.upload_license, name='upload_license'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files during development
'''if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)'''