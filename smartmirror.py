

from tkinter import *
import locale
import threading
import time
import requests
import json
import traceback
import feedparser
from ics import Calendar
import arrow 

from PIL import Image, ImageTk
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

ui_locale = ''
time_format = 24 # 12 eller 24
date_format = "%b %d, %Y" # checka python doc efter strftime() för options
weather_api_token = '99ec389298ab2f08811c983c20819dc9' # skapa konto på https://darksky.net/dev/
ACCESS_KEY = '75f884fbdaff9c3deab8f324682524fd' # skaffa på https://ipstack.com/product
weather_lang = 'sv' 
weather_unit = 'si'
latitude = None
longitude = None
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 15

@contextmanager
def setlocale(name): #thread proof funktion till locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


icon_lookup = {
    'clear-day': "assets/Sun.png",  # klar himmel
    'wind': "assets/Wind.png",   #vind
    'cloudy': "assets/Cloud.png",  # molnigt
    'partly-cloudy-day': "assets/PartlySunny.png",  # växlande molnighet
    'rain': "assets/Rain.png",  # regn
    'snow': "assets/Snow.png",  # snö
    'snow-thin': "assets/Snow.png",  # snöblandat regn
    'fog': "assets/Haze.png",  # dimmigt
    'clear-night': "assets/Moon.png",  # klar natt
    'partly-cloudy-night': "assets/PartlyMoon.png",  # molnig natt
    'thunderstorm': "assets/Storm.png",  # åska
    'tornado': "assests/Tornado.png",    # tornado
    'hail': "assests/Hail.png"  # hagel
}


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize veckodag
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize datum
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #timmar i 12h format
            else:
                time2 = time.strftime('%H:%M') #timmar i 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # uppdatera om tiden ändras
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)

            self.timeLbl.after(200, self.tick)


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
        self.currentlyLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.forecastLbl.pack(side=TOP, anchor=W)
        self.locationLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.locationLbl.pack(side=TOP, anchor=W)
        self.get_weather()

    def get_ip(self):
        try:
            ip_url = "http://jsonip.com/"
            req = requests.get(ip_url)
            ip_json = json.loads(req.text)
            return ip_json['ip']
        except Exception as e:
            traceback.print_exc()
            return "Error: %s. Cannot get ip." % e

    def get_weather(self):
        try:

            if latitude is None and longitude is None:
                # få platts
                location_req_url = "http://api.ipstack.com/%s?access_key=%s" % (self.get_ip(),ACCESS_KEY)
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)

                lat = location_obj['latitude']
                lon = location_obj['longitude']

                location2 = "%s, %s" % (location_obj['city'], location_obj['region_code'])

                # få väder
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, lat,lon,weather_lang,weather_unit)
            else:
                location2 = "Malmoe, Sweden"
                # få väder
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url)
            weather_obj = json.loads(r.text)

            degree_sign= u'\N{DEGREE SIGN}'
            temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
            currently2 = weather_obj['currently']['summary']
            forecast2 = weather_obj["hourly"]["summary"]

            icon_id = weather_obj['currently']['icon']
            icon2 = None

            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]

            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((100, 100), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)

                    self.iconLbl.config(image=photo)
                    self.iconLbl.image = photo
            else:
                # tabort bild
                self.iconLbl.config(image='')

            if self.currently != currently2:
                self.currently = currently2
                self.currentlyLbl.config(text=currently2)
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecastLbl.config(text=forecast2)
            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)
            if self.location != location2:
                if location2 == ", ":
                    self.location = "Cannot Pinpoint Location"
                    self.locationLbl.config(text="Cannot Pinpoint Location")
                else:
                    self.location = location2
                    self.locationLbl.config(text=location2)
        except Exception as e:
            traceback.print_exc()
           # print "Error: %s. Cannot get weather." % e

        self.after(600000, self.get_weather) 




class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'Nyheter'
        self.newsLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP)
        self.get_headlines()

    def get_headlines(self):
        try:
            # remove all children
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
 
            headlines_url = "https://www.svt.se/nyheter/rss.xml"


            feed = feedparser.parse(headlines_url)

            for post in feed.entries[0:5]:
                headline = NewsHeadline(self.headlinesContainer, post.title)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            #print "Error: %s. Cannot get news." % e

        self.after(600000, self.get_headlines)


class NewsHeadline(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')

        image = Image.open("assets/Newspaper.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)
      
        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=LEFT, anchor=N)


class MCalendar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title='Kalender'
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica',28), fg="white", bg="black")
        self.calendarLbl.pack(side = TOP, anchor=W)
        self.calendarEventContainer = Frame(self, bg='black')
        self.calendarEventContainer.pack(side=TOP)
        self.get_events()

    def get_events(self):

        # remove all children
        try:
            for widget in self.calendarEventContainer.winfo_children():
                widget.destroy()

            calendar_url = "https://calendar.google.com/calendar/ical/utbhunle%40skola.malmo.se/private-3866a1216f0582d7cbfaf4806f69bead/basic.ics" #goole ical link
            events = Calendar(requests.get(calendar_url).text).events  #import event
            listOfEvents = []
            now = arrow.utcnow()
            then = now.replace(weeks=1)
            
            for event in events:  #få events i kommande vecka
                if (event.begin>= now) and (event.begin <= then):
                    listOfEvents.append(event)
            
            listOfEvents.sort(key=lambda x: x.begin) #sortera efter datum och tid

            for event in listOfEvents[0:5]: #få de 5 kommande eventen
                    startDate = event.begin
                    month =  str(startDate.month)
                    day = str(startDate.day)
                    text= day+"/"+month+" "+event.name
                    event_label = CalendarEvent(self.calendarEventContainer, text)
                    event_label.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            return "Error getting calendar"
        self.after(600000, self.get_events)


class CalendarEvent(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')
        
        image = Image.open("assets/Calendar.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=TOP, anchor=E)



class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black',cursor='none')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state =True
        self.tk.attributes("-fullscreen", self.state)
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # klocka
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
        # väder
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        # nyheter
        self.news = News(self.bottomFrame)
        self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)
        # kallender
        self.calender = MCalendar(self.bottomFrame)
        self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = True # ändra mellan fullskärm
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", self.state)
        return "break"

if __name__ == '__main__':
    
    w = FullscreenWindow()
    w.tk.mainloop()
