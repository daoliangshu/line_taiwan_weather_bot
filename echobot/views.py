from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from lxml import etree as et
from xml.dom import minidom
import os
import re
import io
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
from django.contrib.staticfiles.templatetags.staticfiles import static

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
def get_env_variable(var_name):
	try:
		return os.environ[var_name]
	except KeyError:
		error_msg = 'Set the {} environment variable'.format(var_name)
SECRET_KEY = get_env_variable('SECRET_KEY')
# WEATHER ACCESS KEY needs to be exported first 
# ( export W[..]KEY = 'your_weather_site_access_key')
data_dic = {'dataid': 'F-C0032-001',
            'authorizationkey': get_env_variable('WEATHER_ACCESS_KEY')}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
	#res = analyse_sentence(event.message.text)
	line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=analyse_sentence(event.message.text))
    )


@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Currently Not Support None Text Message')
    )


@csrf_exempt
def callback(request):
	if request.method == 'POST':
		signature = request.META['HTTP_X_LINE_SIGNATURE']
		body = request.body.decode('utf-8')

		try:
			handler.handle(body, signature)
		except InvalidSignatureError:
			return HttpResponseForbidden()
		except LineBotApiError as e:
			# print(e.status_code)
			# print(e.error.message)
			# print(e.error.details)
			return HttpResponseBadRequest()
		return HttpResponse()
	else:
		
		return HttpResponseBadRequest()


def analyse_sentence(sentence):
	if "天氣" in sentence:
		location = retrieve_location(sentence)
		if location is None:
			return '不好意思，我們沒找到您所輸入的地方!'
		request_url = 'http://opendata.cwb.gov.tw/opendataapi'
		s = requests.Session()
		s.verify = '/'
		file_str = None
		# Request weather as xml file
		r = requests.get(url=request_url, params=data_dic, stream=False, verify=True)
		if r.status_code == 200:
			with open('./file.xml', 'wb') as f:
				for chunk in r:
					if file_str is None:
						file_str = chunk
					else:
						file_str += chunk
					f.write(chunk)
		file = open('./file.xml', 'w')
		file_str = file_str.decode('utf-8')
		# remove xmln namespace for simpler xml manipulation
		file_str = re.sub(' xmlns="[^"]+"', '', file_str, count=1)
		file_str = file_str.encode()
		root = et.fromstring(file_str)
		dataset = root.find('dataset')
		for loc in dataset.iter('location'):
			if loc.find('locationName').text.strip() == location:
				weather = loc.find('weatherElement'). \
						find('time'). \
						find('parameter'). \
						find('parameterName').text
				return '今天'+location + weather
	else:
		return '不好意思， 我不懂您的問題是什麼 。。。'


def retrieve_location(sentence):
	""" Try to find the city ( if provided), and
		format it to formal name for further operations
		return null is not found
	"""
	sub_res = []
	keywords = et.parse(BASE_DIR + "/echobot/keywords.xml").getroot()
	for city_el in keywords.iter('item'):
		city = city_el.get('trans')
		cityreduced = city
		if '市' in city or '縣' in city:
			cityreduced = city[:-1]
		if cityreduced in sentence:
			if '市' in city or '縣' in sentence and city in sentence:
				return city  # perfect match
			else:
				sub_res.append(city)  # candidate
	if len(sub_res) <= 0:
		return None
	elif len(sub_res) == 1:
		return sub_res[0]
	else:
		for c in sub_res:
			if c.endswith('市'):
				return c
		return sub_res[0]
		

	
	


	



