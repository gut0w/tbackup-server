
from django.contrib.auth.models import User, AnonymousUser
from rest_framework import serializers, fields
from rest_framework.authtoken.serializers import AuthTokenSerializer

from server.models import Backup
from server.models.destination.BaseDestination import BaseDestination
from server.models.destination.LocalDestination import LocalDestination
from server.models.destination.SFTPDestination import SFTPDestination


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    auth_token = serializers.Field(source='auth_token')
    
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'auth_token', 'password', 'email', 'is_staff', 'is_superuser')
        read_only_fields = ('is_superuser',)
        write_only_fields = ('password',)
        
    def get_fields(self, *args, **kwargs):
        fields = super(UserSerializer, self).get_fields(*args, **kwargs)
        user = self.context.get('request', None).user
        view = self.context.get('view', None)
        
        if not user.is_staff:
            fields['is_staff'].read_only = True
            
            default = User.objects.get(username='default')
            #hide password from other users
            #if user != default:
            #    fields.pop('password')
            #don't let change 'default' password
            #elif view and getattr(view, 'object', None) and view.object == user:
            #    fields['password'].read_only
        return fields
    
    def restore_object(self, attrs, instance=None):
        if instance is not None:
            user = None
            try:
                user = User.objects.get(username=attrs['username'])
                user.email = attrs.get('email', user.email)
            except User.DoesNotExist:
                user = User(email=attrs['email'], username=attrs['username'])
                #add all destinations by default to the user
                #filter special destinations here (ex.: creating 'staff' property)
                destinations = BaseDestination.objects.all()
                user.basedestination_set.add(*destinations)
            
            password = attrs.get('password', None)
            if password is not None:
                user.set_password(password)
            
            user.is_staff = attrs.get('is_staff', user.is_staff)
            
        return User(**attrs)
    

class LocalDestinationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LocalDestination
        fields = ('directory',)

class SFTPDestinationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SFTPDestination
        fields = ('directory', 'hostname', 'port', 'username', 'key_filename')

class DestinationSerializer(serializers.HyperlinkedModelSerializer):
    type = fields.CharField(max_length=30)
    localdestination = LocalDestinationSerializer(required=False)
    sftpdestination = SFTPDestinationSerializer(required=False)
    
    class Meta:
        model = BaseDestination
        fields = ('id', 'url', 'name', 'type', 'localdestination'
                 , 'sftpdestination', 'date_created', 'date_modified'
                 )
        read_only_fields = ('date_created', 'date_modified')
        
    def get_fields(self, *args, **kwargs):
        fields = super(DestinationSerializer, self).get_fields(*args, **kwargs)
        request = self.context.get('request', None)
        #view = self.context.get('view', None)
        
        #if not admin
        if not request.user.is_staff:
            #remove these fields
            for field in ('type'
                         , 'localdestination'
                         , 'sftpdestination'
                         , 'date_created'
                         , 'date_modified'):
                fields.pop(field)
        
        return fields
    
    def validate(self, attrs):
        return super(DestinationSerializer, self).validate(attrs)
    
    def restore_object(self, attrs, instance=None):
        
        new_attrs = dict()
        new_attrs['name'] = attrs['name']
        
        if instance:
            print instance.__class__
            print instance.__class__.__name__
            print instance
            instance.name = attrs.get('name', instance.name)
            
            if instance.type == 'LocalDestination':
                localdestination = attrs.get('localdestination')
                instance.directory = localdestination.directory if localdestination.directory else instance.localdestination.directory
                
            elif instance.type == 'SFTPDestination':
                sftpdestination = attrs.get('sftpdestination')
                instance.directory = sftpdestination.directory if sftpdestination.directory else instance.sftpdestination.directory
                instance.hostname = sftpdestination.hostname if sftpdestination.hostname else instance.sftpdestination.hostname
                instance.port = sftpdestination.port if sftpdestination.port else instance.sftpdestination.port
                instance.username = sftpdestination.username if sftpdestination.username else instance.sftpdestination.username
                instance.key_filename = sftpdestination.key_filename if sftpdestination.key_filename else instance.sftpdestination.key_filename
                
            return instance
            
        if attrs['type'] == 'LocalDestination':
            new_attrs['directory'] = attrs['localdestination'].directory
            return LocalDestination(**new_attrs)
        elif attrs['type'] == 'SFTPDestination':
            new_attrs['directory'] = attrs['sftpdestination'].directory
            new_attrs['hostname'] = attrs['sftpdestination'].hostname
            new_attrs['port'] = attrs['sftpdestination'].port
            new_attrs['username'] = attrs['sftpdestination'].username
            new_attrs['key_filename'] = attrs['sftpdestination'].key_filename
            return SFTPDestination(**new_attrs)
        else:
            raise Exception('destination type is not implemented')    

class BackupSerializer(serializers.HyperlinkedModelSerializer):
    destination = serializers.Field(source='destination')
    
    class Meta:
        model = Backup
        fields = ('id', 'url')

    def restore_object(self, attrs, instance=None):
        return super(BackupSerializer, self).restore_object(attrs, instance)
    

    