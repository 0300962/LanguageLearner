# LanguageLearner
Bilingual epaper news feed, designed to help me learn a new language.  It's a simple epaper display using a Raspberry Pi Pico W (1st generation) and a 3d-printed stand.  Is it helping? Non lo so, ma io provare.

<img width="753" height="768" alt="Cropped" src="https://github.com/user-attachments/assets/d496edd4-8a72-4ddf-84de-bccc8425464b" />

## Parts list
- Raspberry Pi Pico W with v1.28.0 Micropython firmware
- WeAct 4.2" B&W Epaper display (Waveshare Pico e-Paper 4.2 compatible) and included cable harness
- 3d-printed stand, this one was printed in PLA with supports
- M1.5x10mm machine screw and nut. I'll probably replace this with something slightly less janky when I print the next version of the stand, it's just to stop the screen rocking back in it's slot.
  
<img width="1024" height="768" alt="IMG_20260529_170648917" src="https://github.com/user-attachments/assets/ad337e0d-9e4c-476d-abc0-2bd4512b5572" />

## Operation
This script will:
- Connect to a preset WLAN
-	Send a GET request to a preset URL (in this case an RSS feed)
-	Trim the response down to a few chunks of text
-	Send those chunks for translation by a different API (I'm using https://mymemory.translated.net/)
-	Wrap the text for display on the screen
-	Display on the screen
-	Go to sleep for a few hours

### Notes & Known Issues
- The original Pico W has limited RAM, which will restrict the URLs you can grab before it runs out of space and you get a memory allocation failure. I'm using a pretty simple RSS feed for this reason.
- The Waveshare driver is runnable as a demo to check wiring etc; it also has things like lines, grayscale, partial updates etc - https://www.waveshare.com/wiki/Pico-ePaper-4.2
- The Waveshare driver has only one font, which is about the right size for my use but only handles ASCII so Unicode/UTF16 doesn't render (see the grey boxes in the photos). It's fine for me, but if you want to use a language with lots other characters you'll need to cross that bridge yourself.
<img width="1024" height="768" alt="IMG_20260529_170616333" src="https://github.com/user-attachments/assets/48e7c96d-d15d-457a-ae17-91fcdeb615ce" />

### Instructions
For detailed instructions and default wiring, see the main LanguageLearner.py file.  Assembly is straightforward.
<img width="1024" height="768" alt="IMG_20260529_170520217" src="https://github.com/user-attachments/assets/6d34f6c7-665e-4f2a-8ef0-f8e2b5bd6dfc" />


