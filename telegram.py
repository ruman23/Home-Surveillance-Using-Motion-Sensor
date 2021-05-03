import datetime
from gpiozero import LED
from gpiozero import MotionSensor
import os
import picamera
import schedule
from subprocess import call 
import telepot
from telepot.loop import MessageLoop # Library function to communicate with telegram bot
from threading import Thread
from time import sleep  # Importing the time library to provide the delays in program

camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.framerate = 20
camera.vflip = True


led = LED(17)
led.off()

pir = MotionSensor(4)

now = datetime.datetime.now()

bot = telepot.Bot('set_your_bot_id_here')
globalChatId = set_your_chat_id

videoQueue = []
photoQueue = []
messageQueue = []

retyring = 14400
retyringAfter = 2

commandList = '/hi /time /date /file /video /videoList /deleteVideos /image /imageList /deleteImages /commands' 


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
    print('Connecting to bot...')
    try:
        print(bot.getMe())
        print('connected to bot')
    except:
        print('Could not connect to boot')

def getFileName():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")


def sendTheTextMessage(bot, chat_id):
    while len(messageQueue):
        message = messageQueue.pop(0)
        for tryCount in range(0, retyring):
            try:
                bot.sendMessage(chat_id, message)
            except:
                print('could not send the text message')
                sleep(retyringAfter)
                continue
            break

        
def sendMessage(bot, chat_id, msg):
    messageQueue.append(str(msg))
    textThred = Thread(target = sendTheTextMessage, args = (bot, chat_id))
    textThred.start()

# Delete all the files. But not delete the last `notDeletedFileCount` files
def deleteFiles(bot, chat_id, directory, notDeletedFileCount):
    files = os.listdir(directory)
    totalFiles = len(files)
    files.sort()
    
    for fileIndex in range(0, totalFiles - notDeletedFileCount):
        try:
            os.remove(os.path.join(directory, files[fileIndex]))
        except:
            print('Could not delete the video' + files[fileIndex])
        
    print('Total deleted videos: '+ str(totalFiles - notDeletedFileCount))
    sendMessage(bot, chat_id, str(totalFiles - notDeletedFileCount) + str(' files has been deleted.'))

def captureImage(bot, chat_id):
    #setup directory
    path = getImageDirector()
    fileName = getFileName()
    fileExtension = '.jpeg'
    camera.annotate_text = fileName
    imagePath = path + fileName + fileExtension
        
    sendMessage(bot, chat_id, str("Capturing image..."))
        
    camera.capture(imagePath)
        
    sendPhoto(bot, chat_id, imagePath)
    
def deleteAllImages(bot, chat_id):
    directory = getImageDirector()
    files = os.listdir(directory)
    totalFiles = len(files)
    print('Deleting images')
    for file in files:
        try:
            os.remove(os.path.join(directory, file))
        except:
            print('Could not delete the image')
    sendMessage(bot, chat_id, str(totalFiles) + str(' files has been deleted.'))
    print('Total deleted images: '+ str(totalFiles))
    
def sendTheVideo(bot, chat_id):
    while len(videoQueue):
        videoPath = videoQueue.pop(0)
        try:
            video = open(videoPath, 'rb')
            for tryCount in range(0, retyring):
                try:
                    bot.sendVideo(chat_id, video = open(videoPath, 'rb'))
                    try:
                        deleteVideoThread = Thread(target = deleteFiles, args = (bot, chat_id, getVideoDirectory(), 10))
                        deleteVideoThread.start()
                        deleteVideoThread.join()
                    except:
                        print('Could not delete the files')
                except:
                    print('could not send the video' + videoPath)
                    sleep(retyringAfter)
                    continue
                break
        except:
            print('Invalid video file')
    
def sendThePhoto(bot, chat_id):
    while len(photoQueue):
        imagePath = photoQueue.pop(0)
        for tryCount in range(0, retyring):
            try:
                bot.sendPhoto(chat_id, photo=open(imagePath, 'rb'))
                try:
                    deleteFiles(bot, chat_id, getImageDirector(), 5)
                except:
                    print('Could not delete the images')
            except:
                print('could not send the image')
                sleep(retyringAfter)
                continue
            break
        
def sendPhoto(bot, chat_id, photoPath):
    photoQueue.append(photoPath)
    textThred = Thread(target = sendThePhoto, args = (bot, chat_id))
    textThred.start()

def recordVideo(bot, chat_id, recordingTime):
    #setup directory
    path = getVideoDirectory()
    fileName = getFileName()
    h264Extension = '.h264'
    mp4Extension = '.mp4'
    
    camera.annotate_text = fileName
    camera.start_recording(path + fileName + h264Extension)
    camera.wait_recording(recordingTime)
    camera.stop_recording()
    sendMessage(bot, chat_id, str("Video recorded. Please wait for converting and loading"))
        
    #convert to MP4
    command = "MP4Box -add " + path+ fileName + h264Extension + " " + path+ fileName + mp4Extension
    #print(command)
    call([command], shell=True)
    
    videoQueue.append(path+ fileName + mp4Extension)
    
    t1 = Thread(target = sendTheVideo, args = (bot, chat_id))
    t1.start()

def deletedAllVideos(bot, chat_id):
    directory = getVideoDirectory()
    files = os.listdir(directory)
    totalFiles = len(files)
    print('Total deleted videos: '+ str(totalFiles))
    for file in files:
        try:
            os.remove(os.path.join(directory, file))
        except:
            print('Could not delete the video')
    sendMessage(bot, chat_id, str(totalFiles) + str(' files has been deleted.'))

    
def handle(msg):
    chat_id = msg['chat']['id'] # Receiving the message from telegram
    command = msg['text']   # Getting text from the message
    
    print(command)

    # Comparing the incoming message to send a reply according to it
    if command == '/hi':
        sendMessage(bot, chat_id, str("Hi! Pioneer"))
    elif command == '/time':
        sendMessage(bot, chat_id, str("Time: ") + str(now.hour) + str(":") + str(now.minute) + str(":") + str(now.second))
    elif command == '/date':
        sendMessage(bot, chat_id, str("Date: ") + str(now.day) + str("/") + str(now.month) + str("/") + str(now.year))
    elif command == '/file':
        bot.sendDocument(chat_id, document=open('/home/pi/Documents/mypi/homeAutomation/telegram.py'))
    elif command == '/video':
        recordVideo(bot, chat_id, 20)
    elif command == '/videoList':
        directory = getVideoDirectory()
        sendMessage(bot, chat_id, str(os.listdir(directory)))
    elif command == '/deleteVideos':
        deletedAllVideos(bot, chat_id)
    elif command == '/image':
       captureImage(bot, chat_id)
    elif command == '/imageList':
        directory = getImageDirector()
        sendMessage(bot, chat_id, str(os.listdir(directory)))
    elif command == '/deleteImages':
        deleteAllImages(bot, chat_id)
    elif command == '/commands':
        sendMessage(bot, chat_id, commandList)
    else:
        sendMessage(bot, chat_id, str("Please write a right command. Please send the write commands from the list") + commandList)


def startLiseningMessages():
    try:
        MessageLoop(bot, handle).run_as_thread()
        print ('Listening....')
    except:
        print('MessageLoop error')
        
def main():
    connectToBoot()
    # Start listening to the telegram bot and whenever a message is  received, the handle function will be called.
    try:
        startLiseningMessages()
    except:
        print('startLiseningMessages')
        
    while True:
        try:
            pir.wait_for_motion()
            sendMessage(bot, globalChatId, str('Motion detected'))
            led.on()
            print('Recording video...')
            recordVideo(bot, globalChatId, 10)
        except:
            print('Got error')
        finally:
            led.off()

if __name__ == "__main__":
    main()
