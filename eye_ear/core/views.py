from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import requires_csrf_token, csrf_exempt
from django.db.models import Sum
from django.contrib.auth import login, authenticate
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.conf import settings as django_settings
from django.core.mail import EmailMessage

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

from .models import *
from .serializers import *
from .tokens import account_activation_token

from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_201_CREATED
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

import logging
logger = logging.getLogger(__name__)

from pydub import AudioSegment
from pydub.playback import play  
from gtts import gTTS 

from mutagen.mp3 import MP3
import threading
import multiprocessing 

import os, fnmatch

import html2text
htmlObject = html2text.HTML2Text()
htmlObject.ignore_links = True
htmlObject.emphasis_mark = ""
htmlObject.strong_mark  = ""
htmlObject.ul_item_mark = ""

def response_200(message, data):
    return Response({'status': 'OK', 'message': message, 'data': data}, status=status.HTTP_200_OK)

def response_500(log_msg, e):
    logger.debug(log_msg + str(e))
    return Response({'status': 'error', 'message': 'Something went wrong.' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def response_400(message, log_msg, e):
    if e is not None:
        logger.debug(log_msg + str(e))
    return Response({'status': 'error', 'message': message}, status=status.HTTP_400_BAD_REQUEST)

def response_404():
    return Response({'status': "NOT Found"}, status=status.HTTP_404_NOT_FOUND)

def response_201(message, data):
    return Response({'status': 'Inserted', 'message': message, 'data': data}, status=status.HTTP_201_CREATED)

def response_204(message):
    return Response({'status': 'OK', 'message': message}, status=status.HTTP_204_NO_CONTENT)

def handler404(request, exception, template_name="404.html"):
    response = render(request, template_name)
    response.status_code = 404
    return response

def mainWebsite(request):
    how_many_days = 2
    trending = Blog.objects.filter(is_private = False,audio_complete=1).all()
    for blog in trending:
        clap_objects = Clap.objects.filter(blog=blog)
        if clap_objects.aggregate(Sum('count'))['count__sum']:
            blog.clap_count = clap_objects.aggregate(Sum('count'))['count__sum']
            blog.save()

    if trending.filter(created_at__gte=datetime.now()-timedelta(days=how_many_days)).count() >=6:
        trending = trending.filter(created_at__gte=datetime.now()-timedelta(days=how_many_days))
        
    trending = trending.order_by("-clap_count")[:6]
    must_read_blogs = Blog.objects.filter(must_read = True, is_private = False).order_by("-created_at")[:6]
    data ={
        "trending": trending,
        "must_read_blogs" : must_read_blogs
    }

    return render(request, "home.html",data)

def handleHTML(data):
    finalData = htmlObject.handle(data).replace('`',' ').replace('\n',' ')
    return finalData

def get_description(jsonData):
    description_text = ""    
    for idx,data in enumerate(jsonData["blocks"]):
        if "text" in data["data"]:
            description_text = description_text + handleHTML(data["data"]["text"])
            if len(description_text)>100:
                break
        elif "items" in data["data"]: 
            if data["type"] == "checklist":
                final_section = ""
                for item in data["data"]["items"]:
                    final_section = final_section + item["text"]
                description_text = description_text + handleHTML(final_section)
                if len(description_text)>100:
                    break
            elif data["type"] == "list":
                final_section = ""
                for item in data["data"]["items"]:
                    final_section = final_section + item
                description_text = description_text + handleHTML(final_section)
                
                if len(description_text)>100:
                    break

    return ' '.join(description_text.split()) + "..."

def edit_blog(request,username,blog_id):
    if Blog.objects.filter(id=blog_id).exists():
        blog = Blog.objects.filter(id=blog_id).first()
        if blog.user == request.user:
            if request.method == 'POST' and request.FILES.get('audio',False):
                f = request.FILES.get('audio')
                fs = FileSystemStorage()

                filename = "./audio/"+str(blog_id)+"_final.mp3"
                pattern = str(blog_id)+"_final.mp3"
                
                files = os.listdir('./media/audio')  
                for name in files:  
                    if fnmatch.fnmatch(name, pattern):
                        os.remove("media/audio/{}".format(name))

                files = os.listdir('./static/audio')  
                for name in files:  
                    if fnmatch.fnmatch(name, pattern):
                        os.remove("static/audio/{}".format(name))

                file = fs.save(filename, f)
                fileurl = fs.url(file)
                blog.audio_complete = 2
                blog.save()

            if(json.dumps(blog.body)!="null"):
                blog_body = json.dumps(blog.body)
            else:
                blog_body = {}

            tags = Tag.objects.all()

            for tag in tags:
                if blog.tags.filter(name = tag.name).exists():
                    tag.is_selected = True
                else:    
                    tag.is_selected = False
            
            description_text = ""
            if blog.body:
                description_text = get_description(json.loads(blog.body))

            if blog.title and description_text == "":
                description_text = blog.title

            blog_data = {
                "data": blog_body,
                "id": blog.id,
                "title":blog.title,
                "slug":blog.slug,
                "is_private": blog.is_private,
                "is_new" : blog.is_new,
                "audio_complete":blog.audio_complete,
                "author": blog.user,
                "tags":tags,
                "description_text":description_text
            }

            return render(request, "editing.html", blog_data)
        else:
            return redirect("/{username}/{slug}".format(username=blog.user.slug,slug=blog.slug))
    else:
        return handler404(request,"404")

def view_blog(request,username,blog_slug):
    if User.objects.filter(slug = username).exists():
        user = User.objects.filter(slug = username).first()
        if Blog.objects.filter(user=user ,slug = blog_slug).exists():
            blog = Blog.objects.filter(user=user ,slug = blog_slug).first()
            blog.view_count = blog.view_count + 1
            blog.save()

            if request.user == blog.user or not blog.is_private:
                clap_objects = Clap.objects.filter(blog=blog)
                if clap_objects.count() :
                    clap_count = clap_objects.aggregate(Sum('count'))['count__sum']
                else:
                    clap_count = 0
                voter_count = clap_objects.count()
                for clap_object in clap_objects:
                    if request.user.is_authenticated and request.user.following.filter(email = clap_object.user.email).exists():
                        clap_object.is_followed = True
                    else:
                        clap_object.is_followed = False
                viewer_clap_count = 0
                is_following = False
                is_author = False
                is_saved = False
                author = blog.user

                if request.user.is_authenticated:
                    view, created = Views.objects.get_or_create(user = request.user)
                    view.blogs.add(blog)
                    view.save()

                    if BookMark.objects.filter(user=request.user,blog=blog).exists():
                        is_saved = True
                    if clap_objects.filter(user=request.user).exists():
                        viewer_clap_count = clap_objects.filter(user=request.user).first().count
                    if request.user.following.filter(email = author.email):
                        is_following = True
                    if request.user == author:
                        is_author = True   

                description_text = ""
                if blog.body:
                    description_text = get_description(json.loads(blog.body))

                if blog.title and description_text == "":
                    description_text = blog.title

                blog_data = {
                    "body": json.dumps(blog.body),
                    "id": blog.id,
                    "is_saved":is_saved,
                    "clap_count":clap_count,
                    "voter_count":voter_count,
                    "voters":clap_objects,
                    "viewer_clap_count":viewer_clap_count,
                    "is_following":is_following,
                    "author": author,
                    "title":blog.title,
                    "read_min":blog.reading_time,
                    "created_at":blog.created_at.date(),
                    "is_author":is_author,
                    "blog_link":username+"/"+blog_slug,
                    "audio_complete":blog.audio_complete,
                    "tags":blog.tags.all(),
                    "view_count":blog.view_count,
                    "description_text":description_text
                }
                return render(request, "preview.html",blog_data) 
    
    return handler404(request,"404")

def upload_image_view(request):
    f = request.FILES['image']
    fs = FileSystemStorage()
    filename = "blog/"+str(f).split('.')[0].replace(" ","_")
    file = fs.save(filename, f)
    fileurl = fs.url(file)
    return JsonResponse({'success': 1, 'file': {'url': fileurl}})

def check_image(image_url):
    array_string = ['.png', '.jpg', '.jpeg', '.svg', '.webp']
    for string in array_string:
        if string in image_url:
            return True
    return False

def fetch_link_meta(request):

    url = request.GET.get('url', '')

    response = requests.get(url)

    soup = BeautifulSoup(response.text, features="html.parser")

    metas = soup.find_all('meta')
    links = soup.find_all('link')
    title = str(soup.title.text)

    metaData = '{'
    commaFlag = 0
    if title != "":
        if commaFlag == 0:
            metaData = metaData + '"title":"' + title + '"'
            commaFlag = 1
        else:
            metaData = metaData + ',' + '"title":"' + title + '"'

    for link in links:
        if "type" in link.attrs and 'image' in link.attrs["type"]:
            if commaFlag == 0:
                metaData = metaData + '"' + "image" + \
                    '": { "url" :"' + link.attrs["href"] + '"}'
                commaFlag = 1
            else:
                metaData = metaData + ',' + '"' + "image" + \
                    '": { "url" :"' + link.attrs["href"] + '"}'

    for meta in metas:
        if 'name' in meta.attrs and 'content' in meta.attrs:
            if 'title' in meta.attrs['name'] or ('property' in meta.attrs and 'title' in meta.attrs['property']):
                if commaFlag == 0:
                    metaData = metaData + '"title":"' + \
                        meta.attrs["content"] + '"'
                    commaFlag = 1
                else:
                    metaData = metaData + ',' + '"title":"' + \
                        meta.attrs["content"] + '"'

            elif 'Description' in meta.attrs['name'] or 'description' in meta.attrs['name']:
                if commaFlag == 0:
                    metaData = metaData + '"description":"' + \
                        meta.attrs["content"] + '"'
                    commaFlag = 1
                else:
                    metaData = metaData + ',' + '"description":"' + \
                        meta.attrs["content"] + '"'

            elif '"og:image"' in meta.attrs['name'] and check_image(meta.attrs["content"]):
                if commaFlag == 0:
                    metaData = metaData + '"' + "image" + \
                        '": { "url" :"' + meta.attrs["content"] + '"}'
                    commaFlag = 1
                else:
                    metaData = metaData + ',' + '"' + "image" + \
                        '": { "url" :"' + meta.attrs["content"] + '"}'

        elif 'property' in meta.attrs and "image" in meta.attrs['property'] and check_image(meta.attrs["content"]):
            if commaFlag == 0:
                metaData = metaData + '"' + "image" + \
                    '": { "url" :"' + meta.attrs["content"] + '"}'
                commaFlag = 1
            else:
                metaData = metaData + ',' + '"' + "image" + \
                    '": { "url" :"' + meta.attrs["content"] + '"}'

    metaData = metaData + '}'

    return JsonResponse({'success': 1, 'meta': json.loads(metaData, strict=False)})

@api_view(['POST'])
@requires_csrf_token
def save_data(request):
    try:
        if request.method == "POST" and request.user.is_authenticated:
            data = request.data
            blog, created = Blog.objects.get_or_create(id = data["id"])
            if blog.user == request.user:
                if "title" in data and data['title']:
                    blog.title = data['title']
                if "slug" in data and data["slug"]:
                    blog.slug = data["slug"]
                if "blog_body" in data and data["blog_body"]:
                    blog.body = data['blog_body'].replace("&nbsp;"," ")
                    blog.is_new = False
                    for block in json.loads(blog.body)["blocks"]:
                        if block["type"] == "image" and "file" in block["data"] and "url" in block["data"]["file"]:
                            blog.image = block["data"]["file"]["url"].split("/media/")[1]
                            break

                if "tags" in data and data["tags"]:
                    blog.tags.clear()
                    for tag in data["tags"]:
                        if Tag.objects.filter(name=tag).exists():
                            tagObject = Tag.objects.filter(name=tag).first()
                        else:
                            tagObject = Tag(name = tag)
                            tagObject.save()
                        blog.tags.add(tagObject)
                
                blog.save()
                return response_200("Blog save successfully", BlogSerializer(blog).data)
        return response_400("User not found", "User not found", None)
    except Exception as e:
        return response_500("internal error", e)

@api_view(['POST'])
@requires_csrf_token
def check_slug(request):
    try:
        if request.method == "POST" and request.user.is_authenticated:
            data = request.data
            blog, created = Blog.objects.get_or_create(id = data["id"])
            if blog.user == request.user:
                if Blog.objects.filter(id = data["id"] , user=blog.user).exists():
                    return response_204("Slug found")
                else: 
                    return response_400("Slug not found")

        return response_400("User not found", "User not found", None)

    except Exception as e:
        return response_500("internal error", e)

@api_view(['POST'])
@requires_csrf_token
def add_clap(request):
    try:
        if request.method == "POST" and request.user.is_authenticated:
            data = request.data
            user = request.user
            if Blog.objects.filter(id = data["id"]).exists():
                blog = Blog.objects.filter(id = data["id"]).first()
                if user != blog.user:
                    clap, created = Clap.objects.get_or_create(user = user,blog=blog)
                    clap.count = clap.count + 1
                    clap.save()
                    viewer_clap_count = clap.count
                else:
                    viewer_clap_count = 0

                clap_objects = Clap.objects.filter(blog=blog)
                clap_count = clap_objects.aggregate(Sum('count'))['count__sum']
                voter_count = clap_objects.count()
                voters = ClapSerializer(clap_objects,many=True).data

                clap_data = {
                    "clap_count":clap_count,
                    "voter_count":voter_count,
                    "voters":voters,
                    "viewer_clap_count":viewer_clap_count
                }

                return response_200("Clap save successfully", clap_data)
            else:
                return response_400("Blog not found", "Blog not found", None)
        else:    
            return response_400("User not found", "User not found", None)

    except Exception as e:
        return response_500("internal error", e)

@api_view(['POST'])
@requires_csrf_token
def book_mark(request):
    try:
        if request.method == "POST" and request.user.is_authenticated:
            data = request.data
            user = request.user
            if Blog.objects.filter(id = data["id"]).exists():
                blog = Blog.objects.filter(id = data["id"]).first()
                bookMark, created = BookMark.objects.get_or_create(user = user)
                if data["bookMarkFlag"] ==0:
                    bookMark.blog.remove(blog)
                    return response_200("Blog unsaved successfully", {})
                else:
                    bookMark.blog.add(blog)
                    return response_200("Blog saved successfully", {})
            else:
                return response_400("Blog not found", "Blog not found", None)
        else:    
            return response_400("User not found", "User not found", None)

    except Exception as e:
        return response_500("internal error", e)  

@api_view(['POST'])
@requires_csrf_token
def change_visiblity(request):
    try:
        if request.method == "POST" and request.user.is_authenticated:
            data = request.data
            blog, created = Blog.objects.get_or_create(id = data["id"])
            if blog.user == request.user:
                if "is_private" in data:
                    blog.is_private = data['is_private']
                blog.save()
                return response_200("Visibility Changed successfully",{})
        return response_400("User not found", "User not found", None)

    except Exception as e:
        return response_500("internal error", e)

@api_view(['POST'])
@requires_csrf_token
def add_comment(request):
    try:
        if request.method == "POST":
            data = request.data
            blog, created = Blog.objects.get_or_create(id = data["id"])
            blog.title = data['title']

            if "blog_body" in data:
                blog.body = data['blog_body'].replace("&nbsp;"," ")
            
            blog.save()

            return response_200("Blog save successfully", BlogSerializer(blog).data)

        return response_400("User not found", "User not found", None)

    except Exception as e:
        return response_500("internal error", e)                

def textToAudio(*args):
    array = args[0]
    index = args[1]
    for i in range(index, len(array), 10):
        blog_id = array[i]["blog_id"]
        section_id = array[i]["section_id"]
        text = array[i]["text"]
        slow = array[i]["speed"]
        myobj = gTTS(text = text , lang= 'en' , slow=slow) 
        filename = "static/audio/"+ str(blog_id) +"-"+ str(section_id) +".mp3"
        myobj.save(filename) 

def jsonToAudio(*args):
    blog_id = args[0]
    if Blog.objects.filter(id = blog_id).exists():
        blog= Blog.objects.filter(id = blog_id).first()
        blogBody=blog.body
        blogBody = blogBody.replace('&quot;','"').replace('&lt;','<').replace('&gt;','>').replace('&nbsp;',' ')
        jsonData = json.loads(blogBody) 
        futures = []
        blog.audio_complete = 0
        blog.save()

        pattern = "{}_final.mp3".format(blog_id)
        files = os.listdir('./static/audio')  
        for name in files:  
            if fnmatch.fnmatch(name, pattern):
                os.remove("static/audio/{}".format(name))
        
        files = os.listdir('./media/audio')  
        for name in files:  
            if fnmatch.fnmatch(name, pattern):
                os.remove("media/audio/{}".format(name))

        if blog.title:
            futures.append({"blog_id":blog_id,"section_id":0,"text":blog.title,"speed":False})
        for idx,data in enumerate(jsonData["blocks"]):
            # if 'type' in data and 'level' in data["data"] and data['type'] == 'header' and data["data"]['level'] == 1:
            #     textToAudio(blog_id,idx,handleHTML(data["data"]["text"]),True)
            # elif
            if "quote" == data["type"] and "text" in data["data"]:
                quoteText = "Quote: " + handleHTML(data["data"]["text"])
                if data["data"]["caption"]:
                    quoteText = quoteText + " By " +data["data"]["caption"]
                futures.append({"blog_id":blog_id,"section_id":idx+1,"text": quoteText ,"speed":False})
            elif "text" in data["data"]:
                futures.append({"blog_id":blog_id,"section_id":idx+1,"text": handleHTML(data["data"]["text"]),"speed":False})
            elif "items" in data["data"]: #list,checklist
                if data["type"] == "checklist":
                    final_section = ""
                    for item in data["data"]["items"]:
                        final_section = final_section + item["text"]
                    futures.append({"blog_id":blog_id,"section_id":idx+1,"text":handleHTML(final_section),"speed":False})
                elif data["type"] == "list":
                    final_section = ""
                    for item in data["data"]["items"]:
                        final_section = final_section + item
                    futures.append({"blog_id":blog_id,"section_id":idx+1,"text":handleHTML(final_section),"speed":False})
            
        t1 = threading.Thread(target=textToAudio, args=(futures,0)) 
        t2 = threading.Thread(target=textToAudio, args=(futures,1)) 
        t3 = threading.Thread(target=textToAudio, args=(futures,2)) 
        t4 = threading.Thread(target=textToAudio, args=(futures,3)) 
        t5 = threading.Thread(target=textToAudio, args=(futures,4)) 
        t6 = threading.Thread(target=textToAudio, args=(futures,5)) 
        t7 = threading.Thread(target=textToAudio, args=(futures,6)) 
        t8 = threading.Thread(target=textToAudio, args=(futures,7)) 
        t9 = threading.Thread(target=textToAudio, args=(futures,8)) 
        t10 = threading.Thread(target=textToAudio, args=(futures,9)) 

        t1.start() 
        t2.start() 
        t3.start() 
        t4.start() 
        t5.start() 
        t6.start() 
        t7.start() 
        t8.start() 
        t9.start() 
        t10.start() 

        t1.join() 
        t2.join() 
        t3.join() 
        t4.join() 
        t5.join() 
        t6.join() 
        t7.join() 
        t8.join() 
        t9.join() 
        t10.join()  

        addAllAudio(blog_id,len(jsonData["blocks"])+1)
    else:
        return     

def convertSecToMinAndSecond(seconds):
    mins = seconds // 60
    seconds %= 60
    return mins, seconds

def calculateReadingTime(blog_id):
    audio = MP3("static/audio/"+str(blog_id)+"_final.mp3")
    audio_info = audio.info    
    length_in_secs = int(audio_info.length)
    mins, seconds = convertSecToMinAndSecond(length_in_secs)
    if seconds >0:
        mins = mins+1
    return mins

def addAllAudio(blog_id,section_length):
    blog = Blog.objects.filter(id = blog_id).first()
    result = []
    pattern = str(blog_id)+'-*.mp3'
    files = os.listdir('./static/audio')  
    for name in files:  
        if fnmatch.fnmatch(name, pattern):
            result.append(name)
    final_result = []
    for i in range(0,section_length+1):
        fileName = str(blog_id)+'-'+str(i)+'.mp3'
        if fileName in result:
            final_result.append(fileName)
    result=final_result
    result_audio = AudioSegment.from_mp3("static/audio/"+result[0])
    os.remove("static/audio/"+result[0])
    for audio in result[1:]:
        result_audio = result_audio + AudioSegment.from_mp3("static/audio/"+audio)
        os.remove("static/audio/"+audio)
    result_audio = result_audio + AudioSegment.from_mp3("static/audio/default-thumbnail.mp3")
    result_audio.export("static/audio/"+str(blog_id)+"_final.mp3", format="mp3")
    blog.audio_complete = 1
    blog.reading_time = calculateReadingTime(blog_id)
    blog.save()

@api_view(['POST'])
@requires_csrf_token
def create_audio(request):
    try:
        if request.method == "POST":
            data = request.data
            if Blog.objects.filter(id = data["id"]).exists():
                blog= Blog.objects.filter(id = data["id"]).first()
                if request.user == blog.user:
                    # jsonToAudio(data["id"])
                    p1 = threading.Thread(target=jsonToAudio, args=(data["id"],)) 
                    p1.start() 
                    return response_200("Blog save successfully", {})
        return response_400("User not found", "User not found", None)
    except Exception as e:
        return response_500("internal error", e)                

@api_view(['POST'])
@requires_csrf_token
def follow_user(request):
    try:
        if request.method == "POST" and request.user.is_authenticated:
            data = request.data
            if User.objects.filter(id=data["user_id"]).exists():
                follow_user = User.objects.filter(id=data["user_id"]).first()
                user = request.user
                if user.following.filter(email=follow_user.email).exists():
                    user.following.remove(follow_user)
                    user.save()
                    return response_200("Unfollowed successfully",{"followed":False})
                else:
                    user.following.add(follow_user)
                    user.save()
                    return response_200("followed successfully",{"followed":True})
            else:
                return response_400("User not found", "User not found", None)
        else:    
            return response_400("User not found", "User not found", None)

    except Exception as e:
        return response_500("internal error", e)

@api_view(['GET'])
@requires_csrf_token
def get_audio(request):
    try:
        if request.method == "GET" and request.user.is_authenticated:
            blog_id = request.GET.get('id','')
            if Blog.objects.filter(id=blog_id).exists():
                blog = Blog.objects.filter(id=blog_id).first()
                if blog.audio_complete == 0:
                    return response_204("fail")
                else:
                    return response_200("success",{})
            else:
                return response_400("Blog not found", "Blog not found", None)
        else:    
            return response_400("User not found", "User not found", None)

    except Exception as e:
        return response_500("internal error", e)

def account_activation_sent(request):
    return render(request, 'registration/account_activation_sent.html')

class SignUpForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'first_name','last_name')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Activate Your My Audio Blogs Account'
            message = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.id)),
                'token': account_activation_token.make_token(user),
            })

            email = EmailMessage(
                        subject, message, to=[user.email]
            )
            email.content_subtype = "html"
            email.send()

            return redirect('account_activation_sent')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user,backend='django.contrib.auth.backends.ModelBackend')
        return redirect('/')
    else:
        return render(request, 'registration/account_activation_invalid.html')

def get_by_tag_name(request,tag_name):
    if tag_name == "all":
        blogs = Blog.objects.all().order_by('-created_at')
    else:
        blogs = Blog.objects.filter(tags__name =tag_name).order_by('-created_at')

    final_blogs = []
    for blog in blogs:
        if request.user == blog.user or not blog.is_private:
            blog.clap_objects = Clap.objects.filter(blog=blog)
            blog.clap_count = blog.clap_objects.aggregate(Sum('count'))['count__sum']
            blog.voter_count = blog.clap_objects.count()
            blog.is_saved = False
            blog.viewer_clap_count = 0
            if request.user.is_authenticated:
                if BookMark.objects.filter(user=request.user,blog=blog).exists():
                    blog.is_saved = True
                if blog.clap_objects.filter(user=request.user).exists():
                    blog.viewer_clap_count = blog.clap_objects.filter(user=request.user).first().count
            final_blogs.append(blog)

    data ={
        "tag_name":tag_name,
        "blogs":final_blogs
    }
    return render(request, "tags.html",data)

def create_blog(request):
    if request.user.is_authenticated:
        blog = Blog(user = request.user)
        blog.is_new = True
        blog.save()
        return redirect('/{}/{}/editing'.format(request.user.slug,blog.id))
    else:
        return redirect('signup')     

def user_profile(request,username):
    if User.objects.filter(slug=username).exists():
        user = User.objects.filter(slug=username).first()   
        if request.method == "POST" and request.user == user:
            if request.POST["form-value"] == "0":
                if request.POST['first'] != '':
                    user.first_name = request.POST['first']
                if request.POST['last'] != '':
                    user.last_name = request.POST['last']
                if request.FILES.get('image'):   
                    user.image=request.FILES.get('image')
                if request.POST.get('bio', False) and request.POST["bio"] != 'None':
                    user.bio = request.POST.get('bio')  
                user.save()  
            else:
                if request.POST['blog-id']:
                    blog_id = request.POST['blog-id']
                    if Blog.objects.filter(id = blog_id).exists():
                        blog = Blog.objects.filter(id = blog_id).first()
                        if request.user == blog.user:
                            blog.delete()
                    
        blogs = Blog.objects.filter(user=user).all()
        
        if BookMark.objects.filter(user=user).exists():
            savedBlogs = BookMark.objects.filter(user=user).first().blog.all()
        else:
            savedBlogs = BookMark.objects.filter(user=user)

        if user != request.user:
            if blogs.count():
                blogs = blogs.filter(is_private = False)
            if savedBlogs.count():
                savedBlogs = savedBlogs.filter(is_private = False)

        for blog in blogs:
            blog.clap_objects = Clap.objects.filter(blog=blog)
            blog.clap_count = blog.clap_objects.aggregate(Sum('count'))['count__sum']
            blog.voter_count = blog.clap_objects.count()
            blog.is_saved = False
            blog.viewer_clap_count = 0
            if request.user.is_authenticated:
                if BookMark.objects.filter(user=request.user,blog=blog).exists():
                    blog.is_saved = True
                if blog.clap_objects.filter(user=request.user).exists():
                    blog.viewer_clap_count = blog.clap_objects.filter(user=request.user).first().count
        
        for blog in savedBlogs:
            blog.clap_objects = Clap.objects.filter(blog=blog)
            blog.clap_count = blog.clap_objects.aggregate(Sum('count'))['count__sum']
            blog.voter_count = blog.clap_objects.count()
            blog.is_saved = False
            blog.viewer_clap_count = 0
            if request.user.is_authenticated:
                if BookMark.objects.filter(user=request.user,blog=blog).exists():
                    blog.is_saved = True
                if blog.clap_objects.filter(user=request.user).exists():
                    blog.viewer_clap_count = blog.clap_objects.filter(user=request.user).first().count

        profile_user = False
        is_following = False

        followers = User.objects.filter(following__email=user.email)
        following = user.following.all()
        
        for follower in followers:
            if request.user.is_authenticated and request.user.following.filter(email = follower.email).exists():
                follower.is_following = True
            else:
                follower.is_following = False

        for follower in following:
            if request.user.is_authenticated and request.user.following.filter(email = follower.email).exists():
                follower.is_following = True
            else:
                follower.is_following = False    

        if request.user.is_authenticated:
            request_user = request.user
            if request_user == user:
                profile_user = True
            if request_user.following.filter(email=user.email).exists():
                is_following = True
            

        data ={
            "blogs" : blogs,
            "user":user,
            "profile_user":profile_user,
            "is_following":is_following,
            "followers": followers,
            "following":following,
            "saved": savedBlogs
        }
        return render(request, "profile.html",data)
    return handler404(request,"404")

def preview_blog(request,username,blog_id):
              
    if User.objects.filter(slug = username).exists():
        user = User.objects.filter(slug = username).first()
        if Blog.objects.filter(user=user ,id = blog_id).exists():
            blog = Blog.objects.filter(user=user ,id = blog_id).first()
            if request.user == blog.user or not blog.is_private:
                return redirect("/{username}/{slug}".format(username=blog.user.slug,slug=blog.slug))
    
    return handler404(request,"404")

def terms_and_condition(request):
    return render(request, "termsAndCondition.html")

def privacy(request):
    return render(request, "privacy.html")

def sitemap(request):
    return render(request, 'sitemap.xml', content_type="application/xhtml+xml")

def advertisement(request):
    return render(request, 'ads.html')

def checkGrammar(*args):
    from gingerit.gingerit import GingerIt
    blog_id = args[0]
    if Blog.objects.filter(id = blog_id).exists():
        blog= Blog.objects.filter(id = blog_id).first()
        blogBody=blog.body
        blogBody = blogBody.replace('&quot;','"').replace('&lt;','<').replace('&gt;','>').replace('&nbsp;',' ')
        jsonData = json.loads(blogBody) 
        futures = []
        
        if blog.title:
            futures.append({"blog_id":blog_id,"section_id":0,"text":blog.title,"speed":False})
        for idx,data in enumerate(jsonData["blocks"]):
            if "quote" == data["type"] and "text" in data["data"]:
                quoteText = "Quote: " + handleHTML(data["data"]["text"])
                if data["data"]["caption"]:
                    quoteText = quoteText + " By " +data["data"]["caption"]
                futures.append({"blog_id":blog_id,"section_id":idx+1,"text": quoteText ,"speed":False})
            elif "text" in data["data"]:
                futures.append({"blog_id":blog_id,"section_id":idx+1,"text": handleHTML(data["data"]["text"]),"speed":False})
            elif "items" in data["data"]: #list,checklist
                if data["type"] == "checklist":
                    final_section = ""
                    for item in data["data"]["items"]:
                        final_section = final_section + item["text"]
                    futures.append({"blog_id":blog_id,"section_id":idx+1,"text":handleHTML(final_section),"speed":False})
                elif data["type"] == "list":
                    final_section = ""
                    for item in data["data"]["items"]:
                        final_section = final_section + item
                    futures.append({"blog_id":blog_id,"section_id":idx+1,"text":handleHTML(final_section),"speed":False})

        for text in futures:
            try:
                print("text: ",text)
                parser = GingerIt()
                result=parser.parse(text["text"][:199])    
                print("result: ",result)
            except Exception as e:
                return response_500("internal error", e)