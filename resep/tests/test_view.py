import pytest
from django.urls import reverse
from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from resep.models import Resep, Kategori, Bahan, CookingMethod
from authentication.models import UserProfile
from resep.forms import ResepForm
from bookmark.models import Bookmark
from resep.views import list_resep, create_resep, edit_resep, delete_resep, detail_resep, sanitize_post_data
from django.http import HttpRequest
import html

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user():
    user = User.objects.create_user(
        username="testuser",
        password="testpassword",
        email="test@example.com"
    )
    return user

@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username="adminuser",
        password="adminpassword",
        email="admin@example.com",
        is_staff=True,
        is_superuser=True
    )
    return user

@pytest.fixture
def user_profile(user):
    user_profile = UserProfile.objects.create(user=user)
    return user_profile

@pytest.fixture
def admin_profile(admin_user):
    profile = UserProfile.objects.create(user=admin_user)
    return profile

@pytest.fixture
def non_owner_user():
    user = User.objects.create_user(
        username="nonowner",
        password="testpassword",
        email="nonowner@example.com"
    )
    return user

@pytest.fixture
def non_owner_profile(non_owner_user):
    profile = UserProfile.objects.create(user=non_owner_user)
    return profile

@pytest.fixture
def kategori():
    return Kategori.objects.create(nama="Test Category")

@pytest.fixture
def another_kategori():
    return Kategori.objects.create(nama="Another Category")

@pytest.fixture
def bahan():
    return Bahan.objects.create(nama="Test Ingredient")

@pytest.fixture
def another_bahan():
    return Bahan.objects.create(nama="Another Ingredient")

@pytest.fixture
def cooking_method():
    return CookingMethod.objects.create(nama="Test Cooking Method")

@pytest.fixture
def another_cooking_method():
    return CookingMethod.objects.create(nama="Another Cooking Method")

@pytest.fixture
def resep(user_profile, kategori, bahan, cooking_method):
    resep = Resep.objects.create(
        judul="Test Recipe",
        deskripsi="This is a detailed test description for the recipe that meets the validation requirements.",
        user=user_profile,
        alat="Test equipment: pot, pan, knife, cutting board, measuring spoons",
        bahan="Test ingredients:\n- 2 cups flour\n- 1 cup sugar\n- 3 eggs\n- 2 tablespoons butter\n- 1 teaspoon vanilla extract",
        langkah="Test steps for cooking this recipe:\n1. Preheat oven to 350°F\n2. Mix all dry ingredients in a bowl\n3. Beat eggs in a separate bowl\n4. Combine wet and dry ingredients\n5. Pour batter into greased pan\n6. Bake for 30 minutes or until golden brown",
        kategori=kategori,
        metode_masak=cooking_method,
        bahan_utama=bahan,
        url_foto="http://example.com/image.jpg",
        durasi=30,
        porsi=4,
    )
    return resep

@pytest.fixture
def another_resep(user_profile, another_kategori, another_bahan, another_cooking_method):
    resep = Resep.objects.create(
        judul="Another Test Recipe",
        deskripsi="This is another detailed test description for the recipe with different properties.",
        user=user_profile,
        alat="Different equipment: mixing bowl, whisk, blender, food processor",
        bahan="Different ingredients:\n- 3 cups rice\n- 250g chicken\n- 4 carrots\n- 1 onion\n- 2 cloves garlic",
        langkah="Different steps for cooking this recipe:\n1. Heat oil in a pan\n2. Sauté onions and garlic until fragrant\n3. Add chicken and cook until browned\n4. Add vegetables and cook for 5 minutes\n5. Add rice and stir\n6. Add water and bring to boil\n7. Reduce heat and simmer for 20 minutes",
        kategori=another_kategori,
        metode_masak=another_cooking_method,
        bahan_utama=another_bahan,
        url_foto="http://example.com/another_image.jpg",
        durasi=45,
        porsi=6,
    )
    return resep

@pytest.fixture
def request_factory():
    return RequestFactory()

def setup_request(request, user=None):
    """Set up a request with session and messages"""
    request.session = {}
    setattr(request, '_messages', FallbackStorage(request))
    if user:
        request.user = user
    return request

@pytest.mark.django_db
class TestSanitizePostData:
    def test_sanitize_text_fields(self):
        post_data = {'q': '<script>alert("XSS")</script>', 'other': 'value'}
        sanitized = sanitize_post_data(post_data)

        assert sanitized['q'] == '&lt;script&gt;alert("XSS")&lt;/script&gt;'
        assert sanitized['other'] == 'value'
    def test_sanitize_filter_fields(self):
        post_data = {'category': '&lt;Category&gt;', 'cooking_method': '&lt;Method&gt;', 'main_ingredient': '&lt;Ingredient&gt;'}
        sanitized = sanitize_post_data(post_data)

        assert sanitized['category'] == '<Category>'
        assert sanitized['cooking_method'] == '<Method>'
        assert sanitized['main_ingredient'] == '<Ingredient>'

    def test_sanitize_empty_fields(self):
        post_data = {'category': '', 'q': ''}
        sanitized = sanitize_post_data(post_data)

        assert sanitized['category'] == ''
        assert sanitized['q'] == ''

@pytest.mark.django_db
class TestListResep:
    def test_list_resep_get(self, client, resep):
        response = client.get(reverse('resep:list_resep'))
        assert response.status_code == 200
        assert 'resep_items' in response.context

        assert len(response.context['resep_items'].object_list) > 0

    def test_list_resep_post(self, client, resep):

        response = client.post(reverse('resep:list_resep'), {'q': 'Test Recipe'})
        assert response.status_code == 200
        assert 'resep_items' in response.context
        assert any(r.judul == "Test Recipe" for r in response.context['resep_items'].object_list)

    def test_list_resep_search(self, client, resep):

        response = client.get(reverse('resep:list_resep'), {'q': 'Test Recipe'})
        assert response.status_code == 200

        assert any(r.judul == "Test Recipe" for r in response.context['resep_items'].object_list)


        response = client.get(reverse('resep:list_resep'), {'q': 'ThisShouldNotMatchAnyRecipe12345'})
        assert response.status_code == 200
        assert len(response.context['resep_items'].object_list) == 0

    def test_list_resep_filter_category(self, client, resep, kategori):
        response = client.get(reverse('resep:list_resep'), {'category': kategori.nama})
        assert response.status_code == 200

        assert any(r.kategori.nama == kategori.nama for r in response.context['resep_items'].object_list)

    def test_list_resep_filter_cooking_method(self, client, resep, cooking_method):
        response = client.get(reverse('resep:list_resep'), {'cooking_method': cooking_method.nama})
        assert response.status_code == 200

        assert any(r.metode_masak.nama == cooking_method.nama for r in response.context['resep_items'].object_list)

    def test_list_resep_filter_main_ingredient(self, client, resep, bahan):
        response = client.get(reverse('resep:list_resep'), {'main_ingredient': bahan.nama})
        assert response.status_code == 200

        assert any(r.bahan_utama.nama == bahan.nama for r in response.context['resep_items'].object_list)

    def test_list_resep_multiple_filters(self, client, resep, kategori, cooking_method, bahan):
        response = client.get(reverse('resep:list_resep'), {
            'category': kategori.nama,
            'cooking_method': cooking_method.nama,
            'main_ingredient': bahan.nama
        })
        assert response.status_code == 200
        filtered_recipes = response.context['resep_items'].object_list


        if filtered_recipes:
            for recipe in filtered_recipes:
                assert recipe.kategori.nama == kategori.nama
                assert recipe.metode_masak.nama == cooking_method.nama
                assert recipe.bahan_utama.nama == bahan.nama

    def test_list_resep_sort_options(self, client, resep, another_resep):
        sort_options = [
            ('cooking_time_asc', 'durasi', False),
            ('cooking_time_desc', 'durasi', True),
            ('servings_asc', 'porsi', False),
            ('servings_desc', 'porsi', True),
            ('name_asc', 'judul', False),
            ('name_desc', 'judul', True)
        ]

        for sort_by, field, descending in sort_options:
            response = client.get(reverse('resep:list_resep'), {'sort_by': sort_by})
            assert response.status_code == 200


            all_resep = list(Resep.objects.all())
            if descending:
                all_resep.sort(key=lambda x: getattr(x, field), reverse=True)
            else:
                all_resep.sort(key=lambda x: getattr(x, field))


            page_items = list(response.context['resep_items'].object_list)


            if page_items and all_resep:

                assert getattr(page_items[0], field) == getattr(all_resep[0], field)

    def test_list_resep_pagination(self, client, resep):
        response = client.get(reverse('resep:list_resep'), {'page': 1})
        assert response.status_code == 200
        assert 'resep_items' in response.context


        response = client.get(reverse('resep:list_resep'), {'page': 'invalid'})
        assert response.status_code == 200
        assert 'resep_items' in response.context
        assert response.context['resep_items'].number == 1


        response = client.get(reverse('resep:list_resep'), {'page': '-5'})
        assert response.status_code == 200
        assert response.context['resep_items'].number == 1


        response = client.get(reverse('resep:list_resep'), {'page': '1000'})
        assert response.status_code == 200
        assert response.context['resep_items'].number <= response.context['resep_items'].paginator.num_pages

    def test_list_resep_items_per_page(self, client, resep):

        valid_items = [9, 18, 24, 36]
        for items in valid_items:
            response = client.get(reverse('resep:list_resep'), {'items_per_page': items})
            assert response.status_code == 200
            assert response.context['items_per_page'] == items


        invalid_items = [0, -1, 'abc', 99]
        for items in invalid_items:
            response = client.get(reverse('resep:list_resep'), {'items_per_page': items})
            assert response.status_code == 200
            assert response.context['items_per_page'] == 9

    def test_list_resep_ajax(self, client, resep):
        response = client.get(
            reverse('resep:list_resep'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        assert response.status_code == 200
        assert 'application/json' in response['Content-Type']


        json_data = response.json()
        assert 'recipe_html' in json_data
        assert 'pagination_html' in json_data
        assert 'has_next' in json_data
        assert 'has_previous' in json_data
        assert 'page_number' in json_data
        assert 'total_pages' in json_data
        assert 'categories' in json_data
        assert 'cooking_methods' in json_data
        assert 'main_ingredients' in json_data

    def test_list_resep_bookmark_status_authenticated(self, client, user, resep):

        client.login(username='testuser', password='testpassword')


        user_profile = UserProfile.objects.get(user=user)


        bookmark = Bookmark.objects.create(user=user_profile, resep=resep)


        response = client.get(reverse('resep:list_resep'), {'q': 'Test Recipe'})
        assert response.status_code == 200


        bookmarked_recipes = [r for r in response.context['resep_items'].object_list if r.judul == 'Test Recipe']
        assert len(bookmarked_recipes) > 0
        assert hasattr(bookmarked_recipes[0], 'is_bookmarked')
        assert bookmarked_recipes[0].is_bookmarked

    def test_list_resep_bookmark_status_unauthenticated(self, client, resep):

        response = client.get(reverse('resep:list_resep'), {'q': 'Test Recipe'})
        assert response.status_code == 200


        found_recipes = [r for r in response.context['resep_items'].object_list if r.judul == 'Test Recipe']
        assert len(found_recipes) > 0
        assert hasattr(found_recipes[0], 'is_bookmarked')
        assert not found_recipes[0].is_bookmarked

@pytest.mark.django_db
class TestCreateResep:
    def test_create_resep_get_unauthenticated(self, client):
        response = client.get(reverse('resep:create_resep'))
        assert response.status_code == 302
        assert '/auth/login/' in response.url

    def test_create_resep_get_authenticated(self, client, user):
        client.login(username='testuser', password='testpassword')
        response = client.get(reverse('resep:create_resep'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], ResepForm)


        assert 'csrftoken' in response.cookies

    def test_create_resep_post_valid(self, client, user, kategori, bahan, cooking_method):
        client.login(username='testuser', password='testpassword')


        form_data = {
            'judul': 'New Test Recipe',
            'deskripsi': 'This is a detailed test description for the new recipe that meets the minimum length requirements.',
            'alat': 'Test equipment: pot, pan, knife, cutting board, measuring spoons, blender',
            'bahan': 'Test ingredients:\n- 2 cups flour\n- 1 cup sugar\n- 3 eggs\n- 2 tablespoons butter\n- 1 teaspoon vanilla extract',
            'langkah': 'Test steps for cooking this recipe:\n1. Preheat oven to 350°F\n2. Mix all dry ingredients in a bowl\n3. Beat eggs in a separate bowl\n4. Combine wet and dry ingredients\n5. Pour batter into greased pan\n6. Bake for 30 minutes or until golden brown',
            'kategori': kategori.id,
            'metode_masak': cooking_method.id,
            'bahan_utama': bahan.id,
            'url_foto': 'http://example.com/new_image.jpg',
            'durasi': 45,
            'porsi': 6,
        }

        response = client.post(reverse('resep:create_resep'), form_data)
        assert response.status_code == 302
        assert reverse('resep:list_resep') in response.url


        new_recipe = Resep.objects.filter(judul='New Test Recipe').first()
        assert new_recipe is not None
        assert new_recipe.user.user == user
        assert new_recipe.kategori == kategori
        assert new_recipe.metode_masak == cooking_method
        assert new_recipe.bahan_utama == bahan
        assert new_recipe.durasi == 45
        assert new_recipe.porsi == 6

    def test_create_resep_post_invalid(self, client, user):
        client.login(username='testuser', password='testpassword')


        form_data = {
            'judul': 'Invalid Recipe',

        }

        response = client.post(reverse('resep:create_resep'), form_data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


        assert not Resep.objects.filter(judul='Invalid Recipe').exists()

    def test_create_resep_with_minimal_data(self, client, user, kategori, bahan, cooking_method):
        client.login(username='testuser', password='testpassword')


        form_data = {
            'judul': 'Minimal Recipe',
            'deskripsi': 'This is a minimal description that still meets requirements.',
            'alat': 'Minimal equipment',
            'bahan': '- Ingredient 1\n- Ingredient 2',
            'langkah': 'These are the minimal steps required for this recipe to be valid. They need to be at least 50 characters long.',
            'kategori': kategori.id,
            'metode_masak': cooking_method.id,
            'bahan_utama': bahan.id,
            'url_foto': 'http://example.com/minimal_image.jpg',
            'durasi': 5,
            'porsi': 1,
        }

        response = client.post(reverse('resep:create_resep'), form_data)
        assert response.status_code == 302


        assert Resep.objects.filter(judul='Minimal Recipe').exists()

    def test_create_resep_with_user_profile_creation(self, client):

        new_user = User.objects.create_user(username="newuser", password="newpassword")
        client.login(username="newuser", password="newpassword")


        assert not UserProfile.objects.filter(user=new_user).exists()


        form_data = {
            'judul': 'Profile Creation Recipe',
            'deskripsi': 'This recipe should trigger the creation of a new user profile.',
            'alat': 'Equipment for profile creation test',
            'bahan': '- Ingredient 1\n- Ingredient 2\n- Ingredient 3',
            'langkah': 'These are detailed steps for testing profile creation. They are at least 50 characters long.',
            'kategori': Kategori.objects.first().id,
            'metode_masak': CookingMethod.objects.first().id,
            'bahan_utama': Bahan.objects.first().id,
            'url_foto': 'http://example.com/profile_test_image.jpg',
            'durasi': 15,
            'porsi': 2,
        }

        response = client.post(reverse('resep:create_resep'), form_data)
        assert response.status_code == 302


        assert UserProfile.objects.filter(user=new_user).exists()


        recipe = Resep.objects.get(judul='Profile Creation Recipe')
        assert recipe.user.user == new_user

@pytest.mark.django_db
class TestEditResep:
    def test_edit_resep_get_unauthenticated(self, client, resep):
        response = client.get(reverse('resep:edit_resep', kwargs={'id': resep.id}))
        assert response.status_code == 302
        assert '/auth/login/' in response.url

    def test_edit_resep_get_authenticated_owner(self, client, user, resep):
        client.login(username='testuser', password='testpassword')
        response = client.get(reverse('resep:edit_resep', kwargs={'id': resep.id}))
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], ResepForm)
        assert response.context['editing'] is True
        assert response.context['resep'] == resep


        form = response.context['form']
        assert form.initial['judul'] == resep.judul
        assert form.initial['deskripsi'] == resep.deskripsi
        assert form.instance == resep

    def test_edit_resep_get_authenticated_non_owner(self, client, resep, non_owner_user, non_owner_profile):
        client.login(username='nonowner', password='testpassword')


        response = client.get(reverse('resep:edit_resep', kwargs={'id': resep.id}))
        assert response.status_code == 403

    def test_edit_resep_get_admin_non_owner(self, client, resep, admin_user, admin_profile):

        client.login(username='adminuser', password='adminpassword')


        response = client.get(reverse('resep:edit_resep', kwargs={'id': resep.id}))
        assert response.status_code == 403

    def test_edit_resep_post_valid(self, client, user, resep):
        client.login(username='testuser', password='testpassword')


        form_data = {
            'judul': 'Updated Recipe Title',
            'deskripsi': 'This is an updated description for the recipe that meets the minimum length requirements.',
            'alat': 'Updated equipment: pot, pan, knife, cutting board, measuring spoons',
            'bahan': 'Updated ingredients:\n- 2 cups flour\n- 1 cup sugar\n- 3 eggs\n- 2 tablespoons butter\n- 1 teaspoon vanilla extract',
            'langkah': 'Updated steps for cooking this recipe:\n1. Preheat oven to 350°F\n2. Mix all dry ingredients in a bowl\n3. Beat eggs in a separate bowl\n4. Combine wet and dry ingredients\n5. Pour batter into greased pan\n6. Bake for 30 minutes or until golden brown',
            'kategori': resep.kategori.id,
            'metode_masak': resep.metode_masak.id,
            'bahan_utama': resep.bahan_utama.id,
            'url_foto': resep.url_foto,
            'durasi': resep.durasi,
            'porsi': resep.porsi,
        }

        response = client.post(reverse('resep:edit_resep', kwargs={'id': resep.id}), form_data)
        assert response.status_code == 302
        assert reverse('resep:detail_resep', kwargs={'id': resep.id}) in response.url


        updated_resep = Resep.objects.get(id=resep.id)
        assert updated_resep.judul == 'Updated Recipe Title'
        assert updated_resep.deskripsi == form_data['deskripsi']
        assert updated_resep.alat == form_data['alat']
        assert updated_resep.bahan == form_data['bahan']
        assert updated_resep.langkah == form_data['langkah']

    def test_edit_resep_post_invalid(self, client, user, resep):
        client.login(username='testuser', password='testpassword')


        form_data = {
            'judul': '',
            'deskripsi': resep.deskripsi,
            'alat': resep.alat,
            'bahan': resep.bahan,
            'langkah': resep.langkah,
            'kategori': resep.kategori.id,
            'metode_masak': resep.metode_masak.id,
            'bahan_utama': resep.bahan_utama.id,
            'url_foto': resep.url_foto,
            'durasi': resep.durasi,
            'porsi': resep.porsi,
        }

        response = client.post(reverse('resep:edit_resep', kwargs={'id': resep.id}), form_data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
        assert 'judul' in response.context['form'].errors

    def test_edit_resep_change_category(self, client, user, resep, another_kategori):
        client.login(username='testuser', password='testpassword')


        form_data = {
            'judul': resep.judul,
            'deskripsi': resep.deskripsi,
            'alat': resep.alat,
            'bahan': resep.bahan,
            'langkah': resep.langkah,
            'kategori': another_kategori.id,
            'metode_masak': resep.metode_masak.id,
            'bahan_utama': resep.bahan_utama.id,
            'url_foto': resep.url_foto,
            'durasi': resep.durasi,
            'porsi': resep.porsi,
        }

        response = client.post(reverse('resep:edit_resep', kwargs={'id': resep.id}), form_data)
        assert response.status_code == 302


        updated_resep = Resep.objects.get(id=resep.id)
        assert updated_resep.kategori == another_kategori

    def test_edit_resep_non_existent(self, client, user):
        client.login(username='testuser', password='testpassword')


        response = client.get(reverse('resep:edit_resep', kwargs={'id': 99999}))
        assert response.status_code == 404

@pytest.mark.django_db
class TestDeleteResep:
    def test_delete_resep_get_unauthenticated(self, client, resep):
        response = client.get(reverse('resep:delete_resep', kwargs={'id': resep.id}))
        assert response.status_code == 302
        assert '/auth/login/' in response.url

    def test_delete_resep_get_authenticated_owner(self, client, user, resep):
        client.login(username='testuser', password='testpassword')
        response = client.get(reverse('resep:delete_resep', kwargs={'id': resep.id}))
        assert response.status_code == 200
        assert 'resep' in response.context
        assert response.context['resep'] == resep

    def test_delete_resep_get_authenticated_non_owner(self, client, resep, non_owner_user, non_owner_profile):
        client.login(username='nonowner', password='testpassword')


        response = client.get(reverse('resep:delete_resep', kwargs={'id': resep.id}))
        assert response.status_code == 403

    def test_delete_resep_get_admin_non_owner(self, client, resep, admin_user, admin_profile):

        client.login(username='adminuser', password='adminpassword')


        response = client.get(reverse('resep:delete_resep', kwargs={'id': resep.id}))
        assert response.status_code == 403

    def test_delete_resep_post_success(self, client, user, resep):
        client.login(username='testuser', password='testpassword')


        resep_id = resep.id

        response = client.post(reverse('resep:delete_resep', kwargs={'id': resep.id}))
        assert response.status_code == 302
        assert reverse('resep:list_resep') in response.url


        assert not Resep.objects.filter(id=resep_id).exists()


        from django.contrib.messages import get_messages
        messages = list(get_messages(response.wsgi_request))
        assert any('Recipe successfully deleted!' in str(message) for message in messages)

    def test_delete_resep_post_non_owner(self, client, resep, non_owner_user, non_owner_profile):
        client.login(username='nonowner', password='testpassword')


        response = client.post(reverse('resep:delete_resep', kwargs={'id': resep.id}))
        assert response.status_code == 403


        assert Resep.objects.filter(id=resep.id).exists()

    def test_delete_resep_non_existent(self, client, user):
        client.login(username='testuser', password='testpassword')


        response = client.get(reverse('resep:delete_resep', kwargs={'id': 99999}))
        assert response.status_code == 404

@pytest.mark.django_db
class TestDetailResep:
    def test_detail_resep_exists(self, client, resep):
        response = client.get(reverse('resep:detail_resep', kwargs={'id': resep.id}))
        assert response.status_code == 200
        assert 'resep' in response.context
        assert response.context['resep'] == resep
        assert 'average_rating' in response.context
        assert 'total_ratings' in response.context
        assert 'form' in response.context

    def test_detail_resep_not_exists(self, client):
        response = client.get(reverse('resep:detail_resep', kwargs={'id': 99999}))
        assert response.status_code == 404

    def test_detail_resep_bookmark_status_authenticated(self, client, user, resep, user_profile):
        client.login(username='testuser', password='testpassword')


        Bookmark.objects.create(user=user_profile, resep=resep)

        response = client.get(reverse('resep:detail_resep', kwargs={'id': resep.id}))
        assert response.status_code == 200
        assert response.context['is_bookmarked'] is True

    def test_detail_resep_bookmark_status_unauthenticated(self, client, resep):
        response = client.get(reverse('resep:detail_resep', kwargs={'id': resep.id}))
        assert response.status_code == 200
        assert response.context['is_bookmarked'] is False

    def test_detail_resep_contains_recipe_info(self, client, resep):
        response = client.get(reverse('resep:detail_resep', kwargs={'id': resep.id}))
        assert response.status_code == 200


        content = response.content.decode('utf-8')
        assert resep.judul in content
        assert resep.user.user.username in content


        assert str(resep.durasi) in content
        assert str(resep.porsi) in content

    def test_detail_resep_has_comment_form(self, client, resep):
        response = client.get(reverse('resep:detail_resep', kwargs={'id': resep.id}))
        assert response.status_code == 200


        assert 'form' in response.context
        from komentar.forms import KomentarForm
        assert isinstance(response.context['form'], KomentarForm)