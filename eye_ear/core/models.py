from django.db import models
from django_editorjs import EditorJsField

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

from django.db.models.signals import pre_save
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone_no = models.CharField("Phone No.", max_length=50, null=True, blank=True)
    image = models.ImageField(upload_to ='user/', null=True, blank=True) 
    slug = models.SlugField(max_length=250,null=True,blank=True,unique=True)
    bio = models.CharField(max_length=1500, null=True, blank=True)
    following = models.ManyToManyField("User",blank=True,symmetrical=False)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.username = self.email
        super(User, self).save(*args, **kwargs)

class Tag(models.Model):
    name = models.CharField(max_length = 1000)
    by_default = models.BooleanField(default=False)
    def __str__(self):
        return str(self.name)

class Blog(models.Model):
    title = models.CharField(max_length = 10000)
    body = EditorJsField(editorjs_config ={ "tools": {
            "Image": {
                "config": {
                    "endpoints": {
                        "byFile": 'http://localhost:8000/fileUpload', 
                        "byUrl": 'http://localhost:8000/fetchUrl',
                    },
                    "additionalRequestHeaders":[{"Content-Type":'multipart/form-data'}]
                }
            },
            "header": {
                "class": "Header",
                "shortcut": "CMD+SHIFT+H",
            },
        }},null=True, blank=True)

    image = models.ImageField(upload_to ='blog_image/', null=True, blank=True) 
    lastUpdated = models.DateTimeField('date created', default=timezone.now)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    audio_complete = models.IntegerField(default=0)
    reading_time = models.IntegerField(default=0)
    slug = models.SlugField(max_length=250,null=True,blank=True,unique=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    link_opened = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag,blank=True)
    clap_count = models.IntegerField(default=0)
    is_new = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    must_read = models.BooleanField(default=False)

    def get_absolute_url(self):
        return "/"+ self.user.slug +"/"+self.slug

    def __str__(self):
        return str(self.title)

class Views(models.Model):
    user = models.ForeignKey(User,null=True, blank=True, on_delete=models.SET_NULL)
    blogs = models.ManyToManyField(Blog, blank=True)
    def __str__(self):
        return str(self.id)

class Clap(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    count = models.IntegerField(default=0)
    blog = models.ForeignKey(Blog, null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self):
        return str(self.id)

class Comment(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.CharField(max_length = 10000)
    blog = models.ForeignKey(Blog, null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self):
        return str(self.id)

class BookMark(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    blog = models.ManyToManyField(Blog,blank=True)
    def __str__(self):
        return str(self.id)

def createSlugBlog(instance,new_slug=None):
    slug=slugify(instance.title)
    if new_slug is not None:
        slug=new_slug

    qs=Blog.objects.filter(slug=slug).order_by("-id")
    exists=qs.exists()
    if exists and qs.first() != instance:
        new_slug="%s-%s" %(slug , qs.count())
        return createSlugBlog(instance,new_slug=new_slug)             
    return slug

def slug_generator_blog(sender,instance,*arg,**k):
    if not instance.created_at:
        instance.created_at = timezone.now()
    instance.updated_at = timezone.now()

    instance.slug=createSlugBlog(instance)

pre_save.connect(slug_generator_blog,sender=Blog)

def createSlugUser(instance,new_slug=None):
    slug=slugify(instance.first_name + "-" +instance.last_name)
    if new_slug is not None:
        slug=new_slug

    if User.objects.filter(slug=slug).exists():
        qs=User.objects.filter(slug=slug).order_by("-id")
        new_slug="%s-%s" %(slug , str(qs.first().id))
        return createSlugUser(instance,new_slug=new_slug)   
    return slug

def slug_generator_user(sender,instance,*arg,**k):
    if not instance.slug:
        instance.slug=createSlugUser(instance)

pre_save.connect(slug_generator_user,sender=User)

class Topic(models.Model):
    name = models.CharField(max_length = 1000)
    parent = models.CharField(max_length = 1000)
    url = models.URLField(max_length = 10000)
    def __str__(self):
        return str(self.name)
