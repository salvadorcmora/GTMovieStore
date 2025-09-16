from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Movie, Review


# -------------------------
# Favorites (session-based)
# -------------------------
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
        messages.info(request, f'Removed “{movie.name}” from favorites.')
    else:
        favs.add(id)
        messages.success(request, f'Added “{movie.name}” to favorites.')
    _save_fav_ids(request, favs)
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


# -------------------------
# Movies list / filters
# -------------------------
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
            messages.error(request, "Invalid max price.")

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
        'fav_ids': _get_fav_ids(request),
    }
    return render(request, 'movies/index.html', {'template_data': template_data})


# -------------------------
# Movie detail + reviews
# -------------------------
def show(request, id):
    movie = get_object_or_404(Movie, id=id)
    # Hide reported reviews from everyone
    reviews = Review.objects.filter(movie=movie, is_reported=False)
    template_data = {
        'title': movie.name,
        'movie': movie,
        'reviews': reviews,
    }
    return render(request, 'movies/show.html', {'template_data': template_data})


@login_required
def create_review(request, id):
    if request.method == 'POST':
        comment = (request.POST.get('comment') or '').strip()
        if not comment:
            messages.error(request, 'Comment cannot be empty.')
            return redirect('movies.show', id=id)
        movie = get_object_or_404(Movie, id=id)
        Review.objects.create(movie=movie, user=request.user, comment=comment)
        messages.success(request, 'Review added.')
    return redirect('movies.show', id=id)


@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        messages.error(request, "You can only edit your own reviews.")
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {'title': 'Edit Review', 'review': review}
        return render(request, 'movies/edit_review.html', {'template_data': template_data})

    # POST
    comment = (request.POST.get('comment') or '').strip()
    if not comment:
        messages.error(request, 'Comment cannot be empty.')
        return redirect('movies.show', id=id)

    review.comment = comment
    review.save(update_fields=['comment'])
    messages.success(request, 'Review updated.')
    return redirect('movies.show', id=id)


@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    messages.info(request, 'Review deleted.')
    return redirect('movies.show', id=id)


@login_required
@require_POST
def report_review(request, id, review_id):
    """
    Mark a review as reported; reported reviews no longer show up on the movie page.
    Users cannot report their own reviews.
    """
    review = get_object_or_404(Review, id=review_id, movie_id=id)

    if review.user_id == request.user.id:
        messages.error(request, "You can’t report your own review.")
        return redirect('movies.show', id=id)

    if not getattr(review, 'is_reported', False):
        review.is_reported = True
        review.save(update_fields=['is_reported'])
        messages.success(request, "Thanks — the review was reported and removed.")
    else:
        messages.info(request, "This review has already been reported.")

    return redirect('movies.show', id=id)
