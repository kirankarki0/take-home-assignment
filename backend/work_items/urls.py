"""URL routing for work items API."""
from django.urls import path, re_path
from work_items.views import (
    WorkItemListCreateView,
    WorkItemDetailView,
    WorkItemAnalyseView,
    WorkItemRetryView,
    WorkItemStatusUpdateView,
)

urlpatterns = [
    re_path(r"^work-items/?$", WorkItemListCreateView.as_view(), name="work-item-list-create"),
    re_path(r"^work-items/(?P<item_id>[0-9a-fA-F-]+)/?$", WorkItemDetailView.as_view(), name="work-item-detail"),
    re_path(r"^work-items/(?P<item_id>[0-9a-fA-F-]+)/analyse/?$", WorkItemAnalyseView.as_view(), name="work-item-analyse"),
    re_path(r"^work-items/(?P<item_id>[0-9a-fA-F-]+)/retry/?$", WorkItemRetryView.as_view(), name="work-item-retry"),
    re_path(r"^work-items/(?P<item_id>[0-9a-fA-F-]+)/status/?$", WorkItemStatusUpdateView.as_view(), name="work-item-status"),
]
