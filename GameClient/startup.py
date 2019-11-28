import game
import qrcode
import socket
import uuid
import hashlib
import pygame
from pygame.locals import *
import urllib.request
import json
import ssl
import time
import threading

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT_SIZE = 30

startGame = game.main
clientId = None
connectUser = None
requestFlag = True

ssl._create_default_https_context = ssl._create_unverified_context

def getMacAddress():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

def genClientId():
    md5 = hashlib.md5()
    macAddr = getMacAddress()
    md5.update(macAddr.encode('utf8'))
    return md5.hexdigest()

def terminate():
    global connectUser, requestFlag
    pygame.quit()
    requestFlag = False
    if connectUser != None:
        startGame(connectUser, clientId)
    else:
        quit()

def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, BLACK)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def isReadyToPlay():
    global connectUser, clientId, requestFlag
    while requestFlag:
        try:
            response=urllib.request.urlopen('https://forrestlin.cn/games/isReadyToPlay/%s'%clientId)
            res = response.read().decode('utf-8')
            resJson = json.loads(res)
            print(resJson)
            if resJson['success']: 
                print('connect success, userId = %s\n'%resJson['user']['userId'])
                connectUser = resJson['user']
                requestFlag = False
            else:
                print('connect failed')
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.timeout):
                print('TIME OUT')
        
        time.sleep(2)

def intro():
    global clientId, connectUser
    pygame.init()
    pygame.display.set_caption('意念滑板')
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    pygame.draw.rect(screen, WHITE, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

    clientId = genClientId()
    qrImg = qrcode.make('alicia:%s'%clientId)
    qrImg.save('clientId.png')
    clientImg = pygame.image.load('clientId.png')
    clientImg = pygame.transform.scale(clientImg, (WINDOW_WIDTH, WINDOW_WIDTH))
    screen.blit(clientImg, (0, 0))

    font = pygame.font.SysFont('simsunnsimsun', FONT_SIZE)
    drawText(u'扫码进入游戏', font, screen, (WINDOW_WIDTH - FONT_SIZE * 6) / 2, 450)

    pygame.display.update()

    t = threading.Thread(target=isReadyToPlay)
    t.start()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: #escape quits
                    terminate()
        if connectUser != None:
            terminate()
        clock.tick(60)
    

if __name__ == "__main__":
    intro()
