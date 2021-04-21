from rest_framework import serializers

from .models import *

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField('get_full_name')
    
    def get_full_name(self, obj):
        return obj.first_name +" "+ obj.last_name
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'id', 'slug', 'image','full_name']

class BlogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only = True)

    class Meta:
        model = Blog
        fields = '__all__'

class ClapSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only = True)

    class Meta:
        model = Clap
        fields = '__all__'