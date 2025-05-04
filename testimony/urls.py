from django.urls import path
from .views import *

app_name = 'testimony'

urlpatterns = [
    path("create-testimony/<uuid:product_id>/", create_testimony, name="create_testimony"),
    path("my-testimony/", get_testimony, name="my_testimony"),
    path("edit-testimony/<uuid:testimony_id>/", edit_testimony, name="edit_testimony"),
    path("delete-testimony/<uuid:testimony_id>/", delete_testimony, name="delete_testimony")
]
