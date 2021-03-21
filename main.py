############# IMPORT MODULES ###############
from chatterbot.trainers import ListTrainer
from chatterbot import ChatBot  # module to create a conversation chatbot
import speech_recognition as sr  # module to listen the user speech and transform it in text --> For more information: https://pypi.org/project/SpeechRecognition/
from gtts import gTTS  # google's module to transform text to speech
import os
from pydub import AudioSegment  # module to play audio files
from pydub.playback import play  # module to play audio files
from time import sleep
from datetime import datetime
import wolframalpha  # wolfram alpha API to search things --> For more information: https://pypi.org/project/wolframalpha/
import time
import serial  # module to communicate tha Arduino by serial communication
import wikipedia  # wikipedia API to search things --> For more information: https://pypi.org/project/wikipedia/

############# GLOBALS VARIABLES ###############
global light_status  # variable to know if the light connected in arduino is already on or not (light switch)
light_status = 0

############# WOLFRAM ALPHA API ###############
client = wolframalpha.Client('#########') #wolframalpha user acess tolken 

############# CHATBOT INITIALIZING ###############
bot = ChatBot('Pando')
trainer = ListTrainer(bot)

############# SPEECH RECOGNITION INITIALIZING ###############
rec = sr.Recognizer()


################## FUNCTIONS ##########################
def pandora_speak(message):
    """
    This function get 'message' in string format, transform in audio format and then play this audio
    """
    speak = gTTS(text=message)  # transforming text to speech (TTS) using google's module (gTTS)
    speak.save('pandora.mp3')  # saving this audio file in mp3 format
    print('Bot: ' + message)  # printing in console the bot's response
    song = AudioSegment.from_mp3("pandora.mp3")  # instancing the class to play the audio
    play(song)  # playing the audio
    os.remove('pandora.mp3')  # removing the audio file


def record_audio():
    """
    This function was crated to listen user speech and transform it in text to program (bot) find the response
    :return: a variable in string format with what the user has spoken
    """
    with sr.Microphone() as source:  # using the default microphone configured by own computer
        rec.pause_threshold = 0.5  #
        rec.adjust_for_ambient_noise(source, duration=0.5)  # adapting the sensibility of audio recognition about noises
        print('Say something... ')
        voice_data = ''  # variable that will contain the user speech
        try:
            audio = rec.listen(source, timeout=2)  # listening the user
            voice_data = rec.recognize_google(audio).lower()  # transforming speech to text using google's API
        except sr.UnknownValueError:
            # In case of non-speech, this error will appear and will be treated with this message
            pandora_speak('Sorry sir, I did not undestand. Could you repeat ?')
            voice_data = record_audio()  # here the program try to listen again
        except sr.RequestError:
            # In case of internet service is down, this error will appear and will be treated with this message
            pandora_speak('Sorry, my speech service is down.')
        except sr.WaitTimeoutError:
            # In case of timeout of listening is over, this error will appear and will be treated with this message
            pandora_speak('Sorry sir, I did not undestand. Could you repeat ?')
            voice_data = record_audio()  # here the program try to listen again

        return voice_data


def answer(request):
    """
    This function basely get de request of user, search the bot response in a text file and then return this response

    :param request: The answer or command spoke by the user in string format
    :return: the chatbot response
    """
    response = ''
    response = bot.get_response(request)  # searching the bot response
    if float(response.confidence) > 0.5:  # verify if the response is correct and reliably
        response = str(response)
    else:
        # If the response is not found, the function return the message below:
        response = 'I still don\'t know how to answer this question.'

    return response


def train_chatbot():
    """
    This function is responsible to train the chatbot to learn how to answer the questions
    For this reason, this function must be called in the begin of the program
    """
    for arq in os.listdir('Chat'):  # opening the directory with conversation guides
        chats = open('Chat/' + arq,
                     'r').readlines()  # reading all files with conversation data and storing in a variable
        trainer.train(chats)  # training the chatbot


def search():
    """
    This function is called when the user needs that the chatbot make a quick search in the internet
    """
    pandora_speak('What you want to search, sir?')
    to_search = record_audio()  # store what the user wanna search
    pandora_speak('You said: ' + to_search + ', yes?')  # repeating to confirm the sentence
    confirm = record_audio()  # confirming with 'yes' or 'right'
    print('You: ' + confirm)  # print in console what the user said
    # Comparing if the user confirm the sentence (you can change the confirm words)
    if 'yes' in confirm or 'right' in confirm:
        try:
            # Using de wolfram alpha API to search
            # to learn more, visit: https://pypi.org/project/wolframalpha/
            res = client.query(to_search)
            res = next(res.results).text
            pandora_speak(res)
        except:
            # If they don't find or happens some error, the program try to search in wikipedia
            # to learn more, visit: https://pypi.org/project/wikipedia/
            try:
                res = wikipedia.summary(to_search)
                res = res[:res.find('.') + 1]
                pandora_speak(res)
            except:
                pandora_speak(
                    'I can\'t found your question!')  # if the user question was not found, this message is created
    else:
        # if the user not confirm the sentence, that is, him (or her) said 'no' instead of 'right' or 'yes', this message will appear
        # and the program will try to search again
        pandora_speak('So, I don\'t understand! Repeat please!')
        search()


def send_to_arduino(valor):
    """
    This function was created to control the Arduino device to add extra automation functionalities
    This function communicate with Arduino by the serial port, in this case USB computer port

    :param valor: it's string value that will be used for controlling the Arduino ports
    :return: if the action have done successfully
    """
    try:
        comport = serial.Serial('/dev/ttyUSB0', 9600,
                                timeout=1)  # instancing pyserial module to communicate with Arduino

        PARAM_CARACTER = str.encode(valor)  # encode the variable 'valor' to send to Arduino
        # PARAM_ASCII = str(chr(116))  #  116 = 't'

        # dalay time to connect with Arduino
        time.sleep(1.8)  # between 1.5s a 2s

        comport.write(PARAM_CARACTER)
        # comport.write(PARAM_ASCII)

        VALUE_SERIAL = comport.readline()  # read the serial communication received by Arduino
        done = int(VALUE_SERIAL.decode())  # storing the value

        comport.close()  # closing the connection

        return done  # return the serial data received by Arduino

    except serial.SerialException:
        # If 'SerialException' occurs it means there no serial port connection and the message below will appears
        pandora_speak('No serial port connection')
        return -1


def commands(request):
    """
    This function was created to control based on the user command, what the program must do
    :param request: it's a string variable with the user command
    """
    global light_status  # variable to know if the light connected in arduino is already on or not (light switch)

    if 'search' in request:  # if the user says 'search' in their sentence
        search()

    elif 'what time is it' in request:  # if the user says 'what time is it' in their sentence
        time_now = str(datetime.now().time())  # using the datetime module to catch the current time and date
        time_now = time_now[:9]  # getting only the time data
        pandora_speak(time_now)

    elif ('good morning' in request) or ('good evening' in request) or ('good afternoon' in request):
        # If the user says any greetings, the program will respond with a response greeting, current time and the temperature

        # getting the current time
        time_now = str(datetime.now().time())
        time_now = time_now[:8]
        date_now = str(datetime.now().date())

        # searching the current temperature with wolfram alpha API
        res = client.query('temperature in Rio de Janeiro on' + date_now)
        res = next(res.results).text
        temp = res[res.find(':', 13) + 2:res.find('C', 13) + 1]

        # logic comparison to know what greeting to use
        if int(time_now[:2]) < 12:
            pandora_speak('good morning sir. It\'s ' + time_now + '. And the temperature is ' + temp)
        elif 12 < int(time_now[:2]) < 18:
            pandora_speak('good afternoon sir. It\'s ' + time_now + '. And the temperature is ' + temp)
        else:
            pandora_speak('good evening sir. It\'s ' + time_now + '. And the temperature is ' + temp)

    elif 'wake up' in request:
        pass

    elif 'goodbye' in request:
        pass

    elif 'turn' in request:  # if the user says 'turn' in their sentence, the program know that probably the user want to command the arduino
        # look the arduino sketch
        if 'light' in request:  # if light is on the sentence, the program know what value to send to arduino
            if 'on' in request and light_status == 1:  # logic comparison to know if the port already be activate
                pandora_speak('The light alright on sir')
            elif 'off' in request and light_status == 0:  # logic comparison to know if the port already be deactivate
                pandora_speak('The light alright off sir')
            else:
                result = send_to_arduino(
                    'q')  # sending to Arduino the value corresponding to activate/deactivate the light
                light_status = result  # Arduino response
                if result == 1:
                    pandora_speak('Light on sir')
                elif result == 0:
                    pandora_speak('Light off sir')
                elif result == -1:
                    pass
                else:
                    pandora_speak('Something wrong happened. I suggest you to look my control system.')
        """"
        # this part do the same of above in case of another device to arduino control
        if 'fan' in request and ('on' in request or 'off' in request):
            if 'on' in request and light_status == 1:
                pandora_speak('The fan alright on sir')
            elif 'off' in request and light_status == 0:
                pandora_speak('The fan alright off sir')
            else:
                result = send_to_arduino('v')
                light_status = result
                if result == 1:

                    pandora_speak('fan on sir')
                elif result == 0:

                    pandora_speak('fan off sir')
                elif result == -1:
                    pass
                else:
                    pandora_speak('Something wrong happened. I suggest you to look my control system.')
        else:
            pandora_speak('I don\'t have this function yet')
        """
    elif 'play' in request and 'music' in request:
        # this part is an idea to make the program access my account in Spotify
        pandora_speak('I still don\'t have acess to spotify.')

    elif 'sleep' in request:  # if the user says 'sleep' in their sentence, the program will entry in sleep mode
        pandora_speak('Okay! See you soon!')
        return -1
    else:

        pandora_speak(answer(request))


def recognize_main():
    """
    This function was created as the main of the program
    OBS: this is a trying to make the program to enter and exit a sleep mode
    """
    print("Recognizing Main...")
    while True:
        pandora_speak('Hello sir. I\'m here.')
        req = record_audio()
        print('You: ' + req)
        x = commands(req)
        if x == -1:  # if x == -1 it means that the user won't need the program for hour, so the program will enter in sleep mode
            break  # breaking the loop


################ MAIN PROGRAM ##############################
if __name__ == 'main':
    train_chatbot()
    sleep(1)
    recognize_main()

"""
# trying to make pandora initializing with a hotword
keyword = 'pandora wake up'
while True:
    with sr.Microphone() as source:
        rec.adjust_for_ambient_noise(source)
        try:
            audio = rec.listen(source, timeout=10)
            voice_data = rec.recognize_google(audio).lower()
            if keyword in voice_data:
                recognize_main()
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            print('My server is down')
        except sr.WaitTimeoutError:
            pass
"""
