from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review
from django.contrib import messages
from django.contrib.auth.decorators import login_required


FAV_SESSION_KEY = "favorite_movie_ids"

def _get_fav_ids(request):
    return set(request.session.get(FAV_SESSION_KEY, []))

def _save_fav_ids(request, ids):
    request.session[FAV_SESSION_KEY] = list(ids)
    request.session.modified = True

def toggle_favorite(request, id):
    movie = get_object_or_404(Movie, id=id)
    favs = _get_fav_ids(request)
    if id in favs:
        favs.remove(id)
        messages.info(request, f"Removed “{movie.name}” from favorites.")
    else:
        favs.add(id)
        messages.success(request, f"Added “{movie.name}” to favorites.")
    _save_fav_ids(request, favs)
    # return to referring page or movies index
    return redirect(request.META.get("HTTP_REFERER") or "movies.index")

def favorites(request):
    fav_ids = _get_fav_ids(request)
    movies = Movie.objects.filter(id__in=fav_ids).order_by("name")
    template_data = {
        "title": "My Favorites",
        "movies": movies,
        "fav_ids": fav_ids,
    }
    return render(request, "movies/favorites.html", {"template_data": template_data})


def index(request):
    search_term = request.GET.get('search')
    sort = request.GET.get('sort')
    max_price = request.GET.get('max_price')

    qs = Movie.objects.all()
    if search_term:
        qs = qs.filter(name__icontains=search_term)
    if max_price:
        try:
            qs = qs.filter(price__lte=int(max_price))
        except (TypeError, ValueError):
            pass

    sort_map = {
        'price_asc': 'price',
        'price_desc': '-price',
        'name_asc': 'name',
        'name_desc': '-name',
    }
    if sort in sort_map:
        qs = qs.order_by(sort_map[sort])

    template_data = {
        'title': 'Movies',
        'movies': qs,
        'search_term': search_term or '',
        'sort': sort or '',
        'max_price': max_price or '',
        'fav_ids': _get_fav_ids(request),  # NEW
    }
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie, is_reported=False)  # ← changed
    template_data = {
        'title': movie.name,
        'movie': movie,
        'reviews': reviews,
    }
    return render(request, 'movies/show.html', {'template_data': template_data})


@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)
