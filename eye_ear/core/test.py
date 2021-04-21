from .models import * 
import csv 
import sys,os 

def t(path):
    csv_filepathname="{}Customers.csv".format(path) 
    your_djangoproject_home= path 
    sys.path.append(your_djangoproject_home) 
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

    dataReader = csv.reader(open(csv_filepathname), delimiter=',', quotechar='"') 
    i=0
    for row in dataReader: 
        if i==0:
            i=1
            for topic in range(0,len(row)):
                u=Topic()
                u.name = row[topic]
                u.save()
        elif i==1:
            i=2
            for topic in range(0,len(row)):
                u=Topic.objects.filter(id=topic+1).first()
                u.url = row[topic]
                u.save()
        else:
            for topic in range(0,len(row)):
                u=Topic.objects.filter(id=topic+1).first()
                u.parent = row[topic]
                u.save()

    csv_filepathname="{}medium-tag.csv".format(path) 
    dataReader = csv.reader(open(csv_filepathname), delimiter=',', quotechar='"') 
    for row in dataReader: 
        u=Tag()
        u.name = row[0]
        u.save()
