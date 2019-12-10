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

scale = 2
WINDOW_WIDTH = int(450 * scale)
WINDOW_HEIGHT = int(800 * scale)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT_SIZE = 30

QRCODE_BG_WIDTH = int(267 * scale)
QRCODE_BG_HEIGHT = int(267 * scale)
QRCODE_WIDTH = int(216 * scale)
QRCODE_HEIGHT = int(216 * scale)

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
    tmpUser = connectUser
    connectUser = None
    if tmpUser != None:
        startGame(tmpUser, clientId, intro)
    else:
        quit()

def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, WHITE)
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
    global clientId, connectUser, requestFlag, WINDOW_WIDTH, WINDOW_HEIGHT, scale
    requestFlag = True
    pygame.init()
    pygame.display.set_caption('意念滑板赛')
    displayInfo = pygame.display.Info()
    # if displayInfo.current_h / WINDOW_HEIGHT > displayInfo.current_w / WINDOW_WIDTH:
    #     # fit width
    #     scale = displayInfo.current_w / WINDOW_WIDTH
    #     WINDOW_HEIGHT = int(scale * WINDOW_HEIGHT)
    #     WINDOW_WIDTH = displayInfo.current_w
    # else:
    #     # fit height
    #     scale = displayInfo.current_h / WINDOW_HEIGHT
    #     WINDOW_WIDTH = int(scale * WINDOW_WIDTH)
    #     WINDOW_HEIGHT = displayInfo.current_h
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    pygame.draw.rect(screen, WHITE, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

    bgImg = pygame.image.load('image/startup_bg.jpg')
    bgImg = pygame.transform.scale(bgImg, (WINDOW_WIDTH, WINDOW_HEIGHT))
    screen.blit(bgImg, (0, 0))

    # qrBgImg = pygame.image.load('image/qrcode_bg.png')
    # qrBgImg = pygame.transform.scale(qrBgImg, (QRCODE_BG_WIDTH, QRCODE_BG_HEIGHT))
    # screen.blit(qrBgImg, ((WINDOW_WIDTH - QRCODE_BG_WIDTH) / 2, 345 * scale))

    if clientId == None:
        clientId = genClientId()
    qrImg = qrcode.make('alicia:%s'%clientId)
    qrImg.save('clientId.png')
    clientImg = pygame.image.load('clientId.png')
    clientImg = pygame.transform.scale(clientImg, (QRCODE_WIDTH, QRCODE_HEIGHT))
    screen.blit(clientImg, ((WINDOW_WIDTH - QRCODE_WIDTH) / 2, WINDOW_HEIGHT / 2))

    # font = pygame.font.SysFont('simsunnsimsun', FONT_SIZE)
    font = pygame.font.Font('./fonts/TTTGB-Medium.ttf', FONT_SIZE)
    drawText(u'小程序扫码开始游戏', font, screen, (WINDOW_WIDTH - FONT_SIZE * 9) / 2, WINDOW_HEIGHT / 2 + QRCODE_HEIGHT + 30)

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
