from django.urls import path
from rest_framework import routers

from chef_pencils.views import (
    ChefPencilRecordListCreateView,
    ChefPencilRecordRetrieveUpdateDestroyView,
    ChefPencilRecordRatingView,
    ChefPencilRecordCommentListCreateView,
    ChefPencilRecordCommentLikeView,
    SearchSuggestionsView,
    LatestChefPencilsView,
    ChefPencilRecordCommentDeleteView,
    MyChefPencilRecordListView,
    ChefPencilCategoryView,
    ChefPencilRecordLikeView,
    SavedChefPencilRecordListCreateView,
    SavedChefPencilRecordRetrieveDestroyView
)

app_name = 'Chef Pencils Api'

router = routers.SimpleRouter()

urlpatterns = [
    path('', ChefPencilRecordListCreateView.as_view(), name='chef_pencil_list_create'),
    path('my', MyChefPencilRecordListView.as_view(), name='chef_pencil_my_list'),
    path('<int:pk>', ChefPencilRecordRetrieveUpdateDestroyView.as_view(), name='retrieve_update_destroy'),
    path('<int:pk>/rate', ChefPencilRecordRatingView.as_view(), name='chef_pencil_rate'),
    path('<int:pk>/like', ChefPencilRecordLikeView.as_view(), name='chef_pencil_like'),
    path('<int:pk>/comments', ChefPencilRecordCommentListCreateView.as_view(), name='chef_pencil_comment_list_create'),
    path('comment/<int:pk>/delete', ChefPencilRecordCommentDeleteView.as_view(), name='chef_pencil_comment_delete'),
    path('comment/<int:pk>/like', ChefPencilRecordCommentLikeView.as_view(), name='chef_pencil_comment_like'),
    path('latest_chef_pencils', LatestChefPencilsView.as_view(), name='latest_chef_pencils'),
    path('categories', ChefPencilCategoryView.as_view(), name='categories'),
    path('search_suggestions', SearchSuggestionsView.as_view(), name='search_suggestions'),
    path('saved_chef_pencil_records/', SavedChefPencilRecordListCreateView.as_view(), name='saved_chef_pencil_record'),
    path('saved_chef_pencil_records/<int:pk>', SavedChefPencilRecordRetrieveDestroyView.as_view(), name='saved_chef_pencil_record_retrieve_destroy'),
]

urlpatterns += router.urls