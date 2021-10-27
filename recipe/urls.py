from django.urls import path
from rest_framework import routers

from recipe.views import (
    RecipeListCreateView,
    RecipeRetrieveUpdateDestroyView,
    RecipeRatingView,
    RecipeLikeView,
    RecipeFavoriteCuisinesView,
    TopRatedRecipeView,
    PinnedRecipeView,
    MealOfTheWeekView,
    RecipeCommentListCreateView,
    RecipeCommentDeleteView,
    RecipeCommentLikeView,
    SearchSuggestionsView,
    HomepageBannersView,
    SavedRecipeListCreateView,
    SavedRecipeRetrieveDestroyView,
    PopularRecipesView,
    LatestRecipesView,
    MyRecipeListView,
    UserRecipeListView,
    FeaturedRecipeView,
    UploadVideoView,
    UploadImageView,
    RetrieveRecipeVideoView
)


app_name = 'Recipe api'

router = routers.SimpleRouter()

urlpatterns = [
    path('', RecipeListCreateView.as_view(), name='recipe_list_create'),
    path('my', MyRecipeListView.as_view(), name='recipe_my_list'),
    path('user/<int:user_id>', UserRecipeListView.as_view(), name='recipe_user_list'),
    path('<int:pk>', RecipeRetrieveUpdateDestroyView.as_view(), name='recipe_retrieve_update_destroy'),
    path('<int:pk>/rate', RecipeRatingView.as_view(), name='recipe_rate'),
    path('<int:pk>/like', RecipeLikeView.as_view(), name='recipe_like'),
    path('<int:pk>/comments', RecipeCommentListCreateView.as_view(), name='recipe_comment_list_create'),
    path('comment/<int:pk>/delete', RecipeCommentDeleteView.as_view(), name='recipe_comment_delete'),
    path('comment/<int:pk>/like', RecipeCommentLikeView.as_view(), name='recipe_comment_like'),
    path('saved_recipe/', SavedRecipeListCreateView.as_view(), name='recipe_saved_recipe'),
    path('saved_recipe/<int:pk>', SavedRecipeRetrieveDestroyView.as_view(), name='recipe_saved_recipe_retrieve_destroy'),
    path('favorite_cuisines', RecipeFavoriteCuisinesView.as_view(), name='recipe_favorite_cuisines'),
    path('homepage_banners', HomepageBannersView.as_view(), name='recipe_homepage_banners'),
    path('pinned_meals', PinnedRecipeView.as_view(), name='recipe_pinned'),
    path('meal_of_the_week', MealOfTheWeekView.as_view(), name='meal_of_the_week'),
    path('top_rated_meals', TopRatedRecipeView.as_view(), name='recipe_top_rated'),
    path('featured_meals', FeaturedRecipeView.as_view(), name='recipe_featured'),
    path('search_suggestions', SearchSuggestionsView.as_view(), name='search_suggestions'),
    path('popular_recipes', PopularRecipesView.as_view(), name='recipe_popular'),
    path('latest_user_recipes', LatestRecipesView.as_view(), name='recipe_latest'),
    path('upload_video', UploadVideoView.as_view(), name='upload_video'),
    path('upload_image', UploadImageView.as_view(), name='upload_image'),
    path('video/<int:pk>', RetrieveRecipeVideoView.as_view(), name='recipe_video_retrieve'),
    path('latest_user_recipes', LatestRecipesView.as_view(), name='recipe_latest')
]

urlpatterns += router.urls
