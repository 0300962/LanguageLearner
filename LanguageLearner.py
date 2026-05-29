#Hardware:
#	Raspberry Pi Pico W, v1.28.0 Micropython firmware
#	WeAct 4.2" B&W Epaper display (Waveshare Pico e-Paper 4.2 compatible)
#
#Wiring scheme:
#	EPD Pin		EPD Label	Pico Pin	Pico Label
#	----------------------------------------------
#	1			Busy		17			GP13
#	2			RES			16			GP12
#	3			D/C			11			GP8
#	4			CS			12			GP9
#	5			SCL			14			GP10
#	6			SDA			15			GP11
#	7			GND			38			GND
#	8			VCC			36			3V3(OUT)
#
#For alternate wiring, change the pin assignments in the Epaper driver. And remember that
#the pin numbers in code are the GPIO channel numbers and not the physical pin numbers.
#
#This script will:
#	Connect to a preset WLAN,
#	Send a GET request to a preset URL (in this case an RSS feed)
#	Trim the response down to a few chunks of text
#	Wrap the text for display on the screen
#	Display on the screen
#	Go to sleep for a while
#
#Notes - The original Pico W has limited RAM, which will restrict the URLs you can grab
#		before it runs out of space and you get a memory allocation failure. I'm using
#		a pretty simple RSS feed for this reason.
#		The Waveshare driver is runnable as a demo to check wiring etc; it also has things like
#		lines, grayscale, partial updates etc - https://www.waveshare.com/wiki/Pico-ePaper-4.2#Questions_about_Software
#
#Upload the details of the Wifi to connect to in a file called "wifi.json", at the top level of the Pico
#	{
#		"ssid": "your ssid here",
#		"password": "your wifi password here"
#	}
#
#Upload the "epaper4_2.py" file to the 'lib' folder of the Pico, after editing any pin numbers if required.
#
################################################################################
#How long in hours between updates
sleepTime = 3

#URL to ping to get something to display
#You'll probably want to tweak the parseText function if you change URLs
rawUrl = 'https://en.ilsole24ore.com/rss/italia--attualita.xml'

#URL to send a string to for translation (note langpair value)
translateUrl = 'https://api.mymemory.translated.net/get?langpair=it|en&q='

################################################################################
################################################################################

import network
from time import sleep
import gc
import re
import json
import urequests_2 as urequests #https://github.com/AccelerationConsortium/ac-microcourses/blob/main/docs/courses/hello-world/urequests_2.py
from epaper4_2 import EPD_4in2 #https://github.com/waveshareteam/Pico_ePaper_Code/blob/main/python/Pico-ePaper-4.2_V2.py

wlan = network.WLAN(network.STA_IF)

def connect() -> string:
    with open("wifi.json") as file:
        config = json.load(file)
    
    #Connect to WLAN
    wlan.active(True)
    wlan.connect(config["ssid"], config["password"])
    while wlan.isconnected() == False:
        if rp2.bootsel_button() == 1:
            sys.exit()
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    gc.collect()
    return ip


def disconnect():
    #Shut down the Wifi
    wlan.disconnect()
    wlan.active(False)
    gc.collect()
    return None
    
    
def getRawText(url: string) -> string:
    #Request text from a url - Thanks https://forums.raspberrypi.com/viewtopic.php?t=354514
    try:
        response = urequests.get(url)
        print(f'Status code: {response.status_code}')
        if response.status_code == 200:
            content = response.text
        else:
            return 'Problem getting text from URL'
    except Exception as e:
        print('Error:', e)
        return None
    
    return content


def parseText(raw: string) -> string:
    #Find the date, headline and story from the XML returned from the RSS feed
    print('Parsing text')
    pubDateStart = raw.find('<pubDate>') + 9
    pubDateEnd = raw.find('</pubDate>')
    headlineStart = raw.find('<title><![CDATA[') + 16
    headlineEnd = raw.find(']]></title>')
    storyStart = raw.find('<description><![CDATA[') + 22
    storyEnd = raw.find(']]></description>')
    
    #Truncate the rest of the data to free up RAM again
    raw = raw[0:storyEnd]
    gc.collect()
    
    #Build the article into a string with line breaks, without HTML
    article = raw[pubDateStart:pubDateEnd] + ' /n' + raw[headlineStart:headlineEnd] + ' /n' + raw[storyStart:storyEnd] + '.'
    article = article.replace('<p>', '').replace('</p>', '').replace('<b>', '').replace('</b>', '')
    #Also remove links
    article = re.sub(r"<a .*<\/a>", "", article)
    gc.collect()
    return article


def breakWordsIntoWidth(text: string, width: int) -> [string]:
    # Wraps a paragraph into a reasonable width for display on the screen
    if len(text) < width:
        return [text]
    
    regex = re.compile(r'\s+')
    words = regex.split(text)
    lines = []
    line = ''

    for w in words:
        if not w:
            continue
        if not line:
            # start a new line
            line = w
        elif len(line) + 1 + len(w) <= width:
            # add to current line
            line += ' ' + w
        else:
            # push current line and start a new one
            lines.append(line)
            line = w

    if line:
        lines.append(line)

    return lines
    
    
def getTranslatedText(parsedText: string) -> string:
    #Encodes any spaces to send in API, adds the response to the string
    urlText = parsedText.replace(' ', '%20')
    response = getRawText(translateUrl + urlText) #Returns a string of json data

    translated = ''
    try:
        responseObject = json.loads(response)
        translated = responseObject['responseData']['translatedText']
    except Exception as e:
        print('Error parsing translation:', e)
        translated = 'Problem getting translation'
    
    #Tag the break between sections so it can be delineated later
    return parsedText + ' /nFFF /n' + translated


def displayText(clean: string) -> None:
    #Split, sort and display the text on the screen
    sections = clean.split(' /n')
    yPosition = 10
    
    #Initialise the screen
    epd = EPD_4in2()
    epd.image1Gray.fill(0xff)
    epd.image4Gray.fill(0xff)
    epd.EPD_4IN2_V2_Init()
    
    #Loop through each chunk of text and add to display buffer
    sectionNo = 0
    for s in sections:
        if yPosition > 300:
            #Don't run off the end of the screen
            return None
        
        if s == 'FFF':
            #Change to show translated section
            yPosition += 10
            epd.image1Gray.hline(30, yPosition, 340, epd.black)
            yPosition += 5
            epd.image1Gray.hline(30, yPosition, 340, epd.black)
            yPosition += 10
            sectionNo = 0
            continue
        
        #Break text into lines for display
        lines = breakWordsIntoWidth(s, 45)
        if lines is None:
            continue
        
        for l in lines:
            #Add text to display buffer - (text, left position, top position, colour)
            epd.image1Gray.text(l.strip(), 10, yPosition, epd.black)
            yPosition += 12
        
        sectionNo += 1
        if sectionNo < 3:
            # hline and vline inputs are - (startX, startY, length, colour)
            epd.image1Gray.hline(10, yPosition, 250, epd.black)
            yPosition += 5
    
    #Actually draw update on screen
    epd.EPD_4IN2_V2_Display(epd.buffer_1Gray)
    epd.Sleep()
    print('Finished with display')
    
    gc.collect()    
    return None
    
    
while True:
    #Connect to the wifi
    ip = connect()
    
    #Get a story from an RSS feed
    rawText = getRawText(rawUrl)
    gc.collect()
    
    #Parse the data into something to display
    parsedText = parseText(rawText)
    
    #Translate the text into English for learning purposes
    translatedText = getTranslatedText(parsedText)
    gc.collect()

    #Show the data on the screen
    displayText(translatedText)

    #Disconnect and disable the wifi adapter
    disconnect()
    
    #Wait a while before doing it again
    hours = sleepTime * 60 * 60
    sleep(hours)

