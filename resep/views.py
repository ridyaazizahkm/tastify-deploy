from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse

from komentar.forms import KomentarForm
from .models import Resep
from .forms import ResepForm
from authentication.models import UserProfile
from django.core.paginator import Paginator
from django.db.models import Count
from django.template.loader import render_to_string
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.html import escape
from django.contrib.auth.decorators import login_required
import html

def sanitize_post_data(post_data):
    """
    Sanitize POST data to prevent XSS attacks
    """
    sanitized_data = post_data.copy()
    text_fields = ['q']
    filter_fields = ['category', 'cooking_method', 'main_ingredient']

    for field in text_fields:
        if field in sanitized_data:
            sanitized_data[field] = escape(sanitized_data[field])

    for field in filter_fields:
        if field in sanitized_data and sanitized_data[field]:
            sanitized_data[field] = html.unescape(sanitized_data[field])

    return sanitized_data

@ensure_csrf_cookie
def list_resep(request):
    if request.method == 'POST':
        sanitized_data = sanitize_post_data(request.POST)
        query = sanitized_data.get('q', '')
        category = sanitized_data.get('category', '')
        cooking_method = sanitized_data.get('cooking_method', '')
        main_ingredient = sanitized_data.get('main_ingredient', '')
        sort_by = sanitized_data.get('sort_by', '')
        page_number = sanitized_data.get('page', 1)
        items_per_page = sanitized_data.get('items_per_page', 9)
    else:
        query = request.GET.get('q', '')
        category = html.unescape(request.GET.get('category', ''))
        cooking_method = html.unescape(request.GET.get('cooking_method', ''))
        main_ingredient = html.unescape(request.GET.get('main_ingredient', ''))
        sort_by = request.GET.get('sort_by', '')
        page_number = request.GET.get('page', 1)
        items_per_page = request.GET.get('items_per_page', 9)

    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [9, 18, 24, 36]:
            items_per_page = 9
    except (TypeError, ValueError):
        items_per_page = 9

    base_queryset = Resep.objects.all()

    if query:
        base_queryset = base_queryset.filter(judul__icontains=query)

    category_filtered = base_queryset
    if cooking_method:
        category_filtered = category_filtered.filter(metode_masak__nama=cooking_method)
    if main_ingredient:
        category_filtered = category_filtered.filter(bahan_utama__nama=main_ingredient)

    cooking_method_filtered = base_queryset
    if category:
        cooking_method_filtered = cooking_method_filtered.filter(kategori__nama=category)
    if main_ingredient:
        cooking_method_filtered = cooking_method_filtered.filter(bahan_utama__nama=main_ingredient)

    main_ingredient_filtered = base_queryset
    if category:
        main_ingredient_filtered = main_ingredient_filtered.filter(kategori__nama=category)
    if cooking_method:
        main_ingredient_filtered = main_ingredient_filtered.filter(metode_masak__nama=cooking_method)

    resep_list = base_queryset
    if category:
        resep_list = resep_list.filter(kategori__nama=category)
    if cooking_method:
        resep_list = resep_list.filter(metode_masak__nama=cooking_method)
    if main_ingredient:
        resep_list = resep_list.filter(bahan_utama__nama=main_ingredient)

    if sort_by == 'cooking_time_asc':
        resep_list = resep_list.order_by('durasi')
    elif sort_by == 'cooking_time_desc':
        resep_list = resep_list.order_by('-durasi')
    elif sort_by == 'servings_desc':
        resep_list = resep_list.order_by('-porsi')
    elif sort_by == 'servings_asc':
        resep_list = resep_list.order_by('porsi')
    elif sort_by == 'name_asc':
        resep_list = resep_list.order_by('judul')
    elif sort_by == 'name_desc':
        resep_list = resep_list.order_by('-judul')

    categories = category_filtered.values('kategori__nama').annotate(count=Count('kategori')).order_by('kategori__nama')
    cooking_methods = cooking_method_filtered.values('metode_masak__nama').annotate(count=Count('metode_masak')).order_by('metode_masak__nama')
    main_ingredients = main_ingredient_filtered.values('bahan_utama__nama').annotate(count=Count('bahan_utama')).order_by('bahan_utama__nama')

    categories = [{'kategori': item['kategori__nama'], 'count': item['count']} for item in categories if item['kategori__nama']]
    cooking_methods = [{'metode_masak': item['metode_masak__nama'], 'count': item['count']} for item in cooking_methods if item['metode_masak__nama']]
    main_ingredients = [{'bahan_utama': item['bahan_utama__nama'], 'count': item['count']} for item in main_ingredients if item['bahan_utama__nama']]

    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1

    paginator = Paginator(resep_list, items_per_page)
    total_pages = paginator.num_pages

    if page_number < 1:
        page_number = 1
    elif page_number > total_pages and total_pages > 0:
        page_number = total_pages

    try:
        resep_items = paginator.page(page_number)
    except:
        resep_items = paginator.page(1)

    context = {
        'resep_items': resep_items,
        'query': query,
        'selected_category': category,
        'selected_cooking_method': cooking_method,
        'selected_main_ingredient': main_ingredient,
        'categories': categories,
        'cooking_methods': cooking_methods,
        'main_ingredients': main_ingredients,
        'sort_by': sort_by,
        'items_per_page': items_per_page,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        recipe_html = render_to_string(
            'resep/components/recipe_list.html',
            {'resep_items': resep_items},
            request=request
        )
        pagination_html = render_to_string(
            'resep/components/pagination.html',
            context,
            request=request
        )
        return JsonResponse({
            'recipe_html': recipe_html,
            'pagination_html': pagination_html,
            'has_next': resep_items.has_next(),
            'has_previous': resep_items.has_previous(),
            'page_number': resep_items.number,
            'total_pages': paginator.num_pages,
            'categories': categories,
            'cooking_methods': cooking_methods,
            'main_ingredients': main_ingredients,
            'selected_category': category,
            'selected_cooking_method': cooking_method,
            'selected_main_ingredient': main_ingredient,
        })

    return render(request, 'resep/list_of_resep.html', context)

@login_required(login_url='/auth/login/')
@csrf_protect
def create_resep(request):
    if request.method == 'POST':
        form = ResepForm(request.POST)
        if form.is_valid():
            resep = form.save(commit=False)
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            resep.user = user_profile
            resep.save()
            return redirect('resep:list_resep')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = ResepForm()

    context = {'form': form}
    response = render(request, 'resep/create_resep.html', context)

    response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''), samesite='Lax')
    return response

def detail_resep(request, id):
    resep = get_object_or_404(Resep, pk=id)
    komentar_form = KomentarForm()
    context = {'resep': resep, "average_rating": resep.average_rating(), "total_ratings": resep.total_ratings(), 'form': komentar_form,}

    return render(request, 'resep/detail_resep.html', context)
