from django.urls import path
from .views import *
from django.views.decorators.csrf import csrf_exempt, csrf_protect 

urlpatterns = [
    path('', mainWebsite , name = "mainWebsite"),
    path('fileUpload',csrf_exempt(upload_image_view)), 
    path('fetchLink',csrf_exempt(fetch_link_meta)),
    path('getAudio',csrf_exempt(get_audio),name="get_audio"), 
    path('terms-and-conditions', terms_and_condition, name='terms_and_condition'),
    path('privacy', privacy, name='privacy'),
    path('<username>', user_profile , name = "user_profile"),
    path('tag/<tag_name>', get_by_tag_name , name = "get_by_tag_name"),
    path('<username>/<blog_slug>', view_blog , name = "view_blog"),
    path('<username>/<blog_id>/editing',edit_blog,name="edit_blog"),
    path('<username>/<blog_id>/preview', preview_blog, name='preview_blog'),
    path('saveData/',csrf_exempt(save_data),name="save_data"), 
    path('addClap/',csrf_exempt(add_clap),name="add_clap"), 
    path('bookMarkBlog/',csrf_exempt(book_mark),name="book_mark"), 
    path('changeVisibilty/',csrf_exempt(change_visiblity),name="change_visiblity"), 
    path('followUser/',csrf_exempt(follow_user),name="follow_user"), 
    path('createAudio/',csrf_exempt(create_audio),name="create_audio"), 
    path('account_activation_sent/', account_activation_sent, name='account_activation_sent'),
    path('activate/<uidb64>/<token>/',activate, name='activate'),
    path('signup/', signup, name='signup'),
    path('create/blog/', create_blog, name='create_blog'),
    path('seo/sitemap/', sitemap, name='sitemap'),
    path('advertisement/', advertisement, name='advertisement'),
]