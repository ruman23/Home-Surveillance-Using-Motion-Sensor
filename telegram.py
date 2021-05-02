import datetime
from gpiozero import LED
from gpiozero import MotionSensor
import os
import picamera
import schedule
from subprocess import call 
import telepot
from telepot.loop import MessageLoop # Library function to communicate with telegram bot
from time import sleep  # Importing the time library to provide the delays in program

camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.framerate = 10
camera.vflip = True


led = LED(17)
led.off()

pir = MotionSensor(4)

now = datetime.datetime.now()

bot = telepot.Bot('your_bot_id')
globalChatId = your_chat_id


def getImageDirector():
    directory = '/home/pi/Documents/mypi/homeAutomation/resources/image/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def getVideoDirectory():
    directory = '/home/pi/Documents/mypi/homeAutomation/resources/video/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory
    

def connectToBoot():
    print('[LogId] Connecting to bot...')
    try:
        print(bot.getMe())
        print('[LogId] connected to bot')
    except:
        print('[LogId] Could not connect to boot')
    
    
connectToBoot()

commandList = '/hi /time /date /file /video /videoList /deleteVideos /image /imageList /deleteImages /commands' 

def getFileName():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

# Delete all the files. But not delete the last `notDeletedFileCount` files
def deleteFiles(bot, chat_id, directory, notDeletedFileCount):
    #directory = getVideoDirectory()
    files = os.listdir(directory)
    totalFiles = len(files)
    
    for fileIndex in range(0, totalFiles - notDeletedFileCount):
        os.remove(os.path.join(directory, files[fileIndex]))
        
    print('Total deleted videos: '+ str(totalFiles - notDeletedFileCount))
    bot.sendMessage (chat_id, str(totalFiles - notDeletedFileCount) + str(' files has been deleted.'))

def captureImage(bot, chat_id):
    #setup directory
    path = getImageDirector()
    fileName = getFileName()
    fileExtension = '.jpeg'
    imagePath = path + fileName + fileExtension
        
    bot.sendMessage (chat_id, str("Capturing image..."))
        
    camera.capture(imagePath)
        
    bot.sendMessage (chat_id, str("Image captured. Please wait for loading..."))
        
    bot.sendPhoto(chat_id, photo=open(imagePath, 'rb'), caption = fileName)
    
def deleteAllImages(bot, chat_id):
    directory = getImageDirector()
    files = os.listdir(directory)
    totalFiles = len(files)
    print('Total deleted images: '+ str(totalFiles))
    for file in files:
        os.remove(os.path.join(directory, file))
    bot.sendMessage(chat_id, str(totalFiles) + str(' files has been deleted.'))

def recordVideo(bot, chat_id, recordingTime):
    #setup directory
    path = getVideoDirectory()
    fileName = getFileName()
    h264Extension = '.h264'
    mp4Extension = '.mp4'
        
        
    bot.sendMessage (chat_id, str("Recording video..."))
    camera.start_recording(path + fileName + h264Extension)
    camera.wait_recording(recordingTime)
    camera.stop_recording()
    bot.sendMessage (chat_id, str("Video recorded. Please wait for converting"))
        
    #convert to MP4
    command = "MP4Box -add " + path+ fileName + h264Extension + " " + path+ fileName + mp4Extension
    #print(command)
    call([command], shell=True)
        
    bot.sendMessage (chat_id, str("Video converted. Please wait for loading"))
        
    bot.sendVideo(chat_id, video = open(path+ fileName + mp4Extension, 'rb'))
    
      #delete h264 video file
    os.remove(path+ fileName + h264Extension) 
    deleteFiles(bot, chat_id, path, 5)

def deletedAllVideos(bot, chat_id):
    directory = getVideoDirectory()
    files = os.listdir(directory)
    totalFiles = len(files)
    print('Total deleted videos: '+ str(totalFiles))
    for file in files:
        os.remove(os.path.join(directory, file))
    bot.sendMessage (chat_id, str(totalFiles) + str(' files has been deleted.'))
    
def handle(msg):
    chat_id = msg['chat']['id'] # Receiving the message from telegram
    command = msg['text']   # Getting text from the message
    
    print ('[LogId] Received:')
    print(command)

    # Comparing the incoming message to send a reply according to it
    if command == '/hi':
        bot.sendMessage (chat_id, str("Hi! Pioneer"))
    elif command == '/time':
        bot.sendMessage(chat_id, str("Time: ") + str(now.hour) + str(":") + str(now.minute) + str(":") + str(now.second))
    elif command == '/date':
        bot.sendMessage(chat_id, str("Date: ") + str(now.day) + str("/") + str(now.month) + str("/") + str(now.year))
    elif command == '/file':
        bot.sendDocument(chat_id, document=open('/home/pi/Documents/mypi/homeAutomation/telegram.py'))
    elif command == '/video':
        recordVideo(bot, chat_id, 20)
    elif command == '/videoList':
        directory = getVideoDirectory()
        bot.sendMessage (chat_id, str(os.listdir(directory)))
    elif command == '/deleteVideos':
        deletedAllVideos(bot, chat_id)
    elif command == '/image':
       captureImage(bot, chat_id)
    elif command == '/imageList':
        directory = getImageDirector()
        bot.sendMessage (chat_id, str(os.listdir(directory)))
    elif command == '/deleteImages':
        deleteAllImages(bot, chat_id)
    elif command == '/commands':
        bot.sendMessage(chat_id, commandList)
    else:
        bot.sendMessage(chat_id, str("Please write a right command. Please type `/commands` for command list"))


def startLiseningMessages():
    try:
        MessageLoop(bot, handle).run_as_thread()
        print ('[LogId] Listening....')
    except:
        print('[LogId] MessageLoop error')

# Start listening to the telegram bot and whenever a message is  received, the handle function will be called.
try:
    startLiseningMessages()
except:
    print('startLiseningMessages')

while True:
    try:
        pir.wait_for_motion()
        bot.sendMessage(globalChatId, str('Motion detected'))
        led.on()
        recordVideo(bot, globalChatId, 20)
    except:
        print('Got error')
    finally:
        led.off()