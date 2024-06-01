# app/routes.py
from flask import Blueprint, render_template
from app.modules.AIService import AIService


url = Blueprint('url', __name__)

@url.route('/')
def home():
    return render_template('home.html')

@url.route("/upload", methods = ['POST'])
def upload( ):
    return AIService.uploadFile()

@url.route("/get_file", methods =['POST'])
def getFile( ):
    return AIService.getFile()

