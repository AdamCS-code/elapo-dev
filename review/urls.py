from django.urls import path
from .views import get_report, create_fraud_report, update_fraud_report, delete_fraud_report
from .views import get_review, create_review, update_review, delete_review

app_name = 'review'

urlpatterns = [
    path("report-fraud/<uuid:order_id>/", create_fraud_report, name="report_fraud"),
    path("my-report/", get_report, name="my_report"),
    path("update-report/<uuid:report_id>", update_fraud_report, name="update_report"),
    path("delete-report/<uuid:report_id>", delete_fraud_report, name="delete_report"),

    path("create-review/<uuid:order_id>/", create_review, name="create_review"),
    path("my-review/", get_review, name="my_review"),
    path("update-review/<uuid:review_id>", update_review, name="update_review"),
    path("delete-review/<uuid:review_id>", delete_review, name="delete_review")
]
