from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='movies.index'),
    path('<int:id>/', views.show, name='movies.show'),
    path('<int:id>/review/create/', views.create_review, name='movies.create_review'),
    path('<int:id>/review/<int:review_id>/edit/', views.edit_review, name='movies.edit_review'),
    path('<int:id>/review/<int:review_id>/delete/', views.delete_review, name='movies.delete_review'),
    path('favorites/', views.favorites, name='movies.favorites'),
    path('<int:id>/toggle-favorite/', views.toggle_favorite, name='movies.toggle_favorite'),
    path('<int:id>/reviews/<int:review_id>/report/', views.report_review, name='movies.report_review'),
    path("petitions/", views.petitions_list, name="movies.petitions_list"),
    path("petitions/new/", views.petitions_create, name="movies.petitions_create"),
    path("petitions/<int:id>/vote/", views.petition_vote_yes, name="movies.petition_vote_yes"),
    
]

