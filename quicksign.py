#! /usr/bin/python
# -*- coding:utf-8 -*-


import os.path
import glob
import urllib.request
import hashlib
import pymongo, gridfs
from pymongo import MongoClient


import PIL
from PIL import Image, ImageFile

from flask import Flask, make_response, render_template
from flask import request

app = Flask(__name__)

__author__ = 'bouba'

links = open('urls.txt', 'r')

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36')]
urllib.request.install_opener(opener)


## Save Image
def save_image(image, path):
    image.save(path, 'png')
 
# From RGB(0,1,2) to grayscale
def grayscale(picture):
    res=PIL.Image.new(picture.mode, picture.size)
    width, height = picture.size
    
    for i in range(0, width):
        for j in range(0, height):
            pixel=picture.getpixel((i,j))
            avg=int((pixel[0]+pixel[1]+pixel[2])/3)
            res.putpixel((i,j),(avg,avg,avg))
    save_image(res,transform+'.png')
    
# MD5 hash calc  
def hash(path):
    print('MD5 of the file : ' + hashlib.md5(path.encode()).hexdigest())
    

#MongoDB connection
client = MongoClient('localhost', 27017)

db = client['qs'] # the database

grid_fs = gridfs.GridFS(db, "niveaugris", disable_md5=False) # niveaugris is the collection name

    
for link in links:
    link = link.strip()
    name = link.rsplit('/', 1)[-1]
    os.makedirs('images', exist_ok=True)
    os.makedirs('grayscale_pics', exist_ok=True)
    transform = os.path.join('grayscale_pics', name)
    filename = os.path.join('images', name)
    if not os.path.isfile(filename):
        print('Downloading: ' + filename+'.jpg')       
        try:
            color = urllib.request.urlretrieve(link, filename+'.jpg')
            #hash(filename)
            for fname in glob.glob('images/*.*'):
                image = Image.open(fname)
                # Image size
                width, height = image.size
                print('Image size is : ' , width, 'x' , height)
                gray = grayscale(image)
        except Exception as inst:
            print(inst)
            print(' Error : file not found. Continuing.')

            
# Storing grayscale pics in MongoDB           
for f in glob.glob('grayscale_pics/*.*'):
    rem = open(f,'rb')
    md5=hash(f)
    myfiles = grid_fs.put(rem,content_type='img/png', filename=f.rsplit('/', 1)[-1], mode='rb')
    outputdata = grid_fs.get(myfiles).read()
   
### Flask ########    

@app.route('/')
def index():
    return render_template('index.html')

# Display an image by name e.g localhost:5000/images/88.png            
@app.route('/images/<filename>')
def get_file(filename):
        f = grid_fs.get_last_version(filename).read()
        r = app.response_class(f, direct_passthrough=True, mimetype='image/png')       
        return r

        
@app.route('/image/<md5>')
def hash_images(md5):        
    out = grid_fs.get_last_version(md5="4b104163f8926cea16e664fe923f6338").read()
    img = app.response_class(out, direct_passthrough=True, mimetype='image/png')
    return img

if __name__ == '__main__':
    app.run()

    

