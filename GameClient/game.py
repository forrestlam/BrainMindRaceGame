import pygame, random, sys, os, time, math
from pygame.locals import *
import _thread as thread
import argparse
import multiprocessing    # for processing osc stream

from pythonosc import dispatcher as dsp
from pythonosc import osc_server
from pythonosc import udp_client
import urllib.request
import json
import io
import threading
from urllib import parse

event = multiprocessing.Event()

scale = 1.2
WINDOWWIDTH = int(450 * scale)
WINDOWHEIGHT = int(800 * scale)
TEXTCOLOR = (255, 255, 255)
BACKGROUNDCOLOR = (0, 0, 0)
MASKCOLOR = (0, 0, 0, 180)
WHITECOLOR = (255, 255, 255)
FPS = 60
BADDIEMINSIZE = 10
BADDIEMAXSIZE = 40
BADDIESPEED = 8
MINADDNEWBADDIERATE = 107
MAXADDNEWBADDIERATE = 87
MINADDNEWSTARRATE = 20
MAXADDNEWSTARRATE = 10
INITPLAYERMOVERATE = 5
PLAYERMOVERATE = 5
GAMEDURATION = 60 # game duration

IMAGE_WIDTH = 45
WHOLE_IMAGE_WIDTH = 60
scale = 1

count=3

# for muse tracking
playerRect = None
gameParams = None
oscProcess = None

concenList = []

MINY = -0.5
MAXY = 1

connectUser = None
clientId = None
returnCallback = None

PLAYER_MIN_X = int(55 * scale)
PLAYER_MAX_X = WINDOWWIDTH - PLAYER_MIN_X

min_x = 120
max_x = WINDOWWIDTH - 35
x_data = list(range(min_x, max_x, int((max_x-min_x)/IMAGE_WIDTH)))
ALL_DATA = []   

def concen_handler(unused_addr, args, value):
    speed = (1-value) * 30
    # update beta values
    beta = args[0]['beta']
    beta.insert(len(beta), value)
    beta.remove(beta[0])
    args[0]['beta'] = beta
    # calculate speed
    speed = min(speed, 30)
    speed = max(speed, 10)
    args[0]['speed'] = speed
    args[0]['concen'] = value * 100
    event.set()    
    
def acc_handler(unused_addr, args, x, y, z):
    # normalize y
    global WINDOWWIDTH, playerRect
    rate = (y - MINY) / (MAXY - MINY)
    if rate > 1:
        rate = 1
    if rate < 0:
        rate = 0
    x = WINDOWWIDTH * rate + 30
    args[0]['left'] = PLAYER_MIN_X + x
    event.set()

def start_osc(ip, port, info):
    dispatcher = dsp.Dispatcher()
    #dispatcher.map("/muse/algorithm/concentration", concen_handler, info)
    dispatcher.map("/muse/elements/delta_absolute", concen_handler, info)
    dispatcher.map("/muse/acc", acc_handler, info)

    server = osc_server.ThreadingOSCUDPServer(
        (ip, port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()    

def terminate():
    global oscProcess, clientId, connectUser, returnCallback, count
    if connectUser:
        response = urllib.request.urlopen('https://forrestlin.cn/games/closeConnection/%s/%s'%(clientId, connectUser['userId']))
        res = response.read().decode('utf-8')
        resJson = json.loads(res)
        if not resJson['success']:
            print('Failed to close connection, reason: %s'%resJson['errMsg'])
        else:
            print('Succeed to close connection')
    pygame.quit()
    oscProcess.terminate()
    count = 3
    # go back the startup page
    if returnCallback:
        returnCallback()
    else:
        sys.exit()

def sampleAllData():
    global ALL_DATA
    if len(ALL_DATA) < WHOLE_IMAGE_WIDTH:
        return
    step = int(len(ALL_DATA) / WHOLE_IMAGE_WIDTH)
    data = []
    for i in range(0, len(ALL_DATA), step):
        if len(data) >= WHOLE_IMAGE_WIDTH:
            break
        data.append(ALL_DATA[int(i)])
    ALL_DATA = data
    
def waitForPlayerToPressKey():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: #escape quits
                    terminate()
                return

def playerHasHitBaddie(playerRect, baddies):
    for b in baddies:
        if playerRect.colliderect(b['rect']):
            return True
    return False

def playerHasHitStar(playerRect, stars):
    for s in stars:
        if playerRect.colliderect(s['rect']):
            stars.remove(s)
            return True
    return False    

def drawText(text, font, surface, x, y, textColor=TEXTCOLOR):
    textobj = font.render(text, 1, textColor)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def uploadScore(score, concenList):
    global clientId, connectUser, ALL_DATA
    if connectUser == None:
        return
    waves = ALL_DATA
    waves = [max(i , 0.05) * 10 for i in waves]
    avgCon = 80
    if len(concenList) > 0:
        avgCon = sum(concenList) / len(concenList)
        avgCon = min(avgCon, 100)
    data = {'clientId': clientId, 'userId': connectUser['userId'], 'score': score, 'concen': avgCon, 'waves': ','.join(map(str, waves))}
    data = parse.urlencode(data).encode('utf-8')
    if clientId != None and connectUser != None:
        response = urllib.request.urlopen('https://forrestlin.cn/games/finishGame', data=data)
        res = response.read().decode('utf-8')
        resJson = json.loads(res)
        if not resJson['success']:
            print('Failed to upload score, reason: %s'%resJson['errMsg'])
        else:
            print('Succeed to upload score')


def drawLines(surface, x_data, y_data):
    global ALL_DATA
    max_y = 36
    points = []
    ALL_DATA.append(y_data[-1])
    r = len(x_data) if len(y_data) > len(x_data) else len(y_data)
    for i in range(r):
        y_data[i] = max_y * y_data[i] + 30
        points.append((x_data[i], y_data[i]))
    if len(points) > 0:
        linerect = pygame.draw.aalines(surface, (255, 255, 255), False, points, 5)
        linerect.topleft = (0, 0)
        pygame.display.flip()


def drawWholeLines(surface, baseline):
    global gameParams, WINDOWHEIGHT, ALL_DATA
    points = []
    min_x = int((WINDOWWIDTH - 313) / 2 + 20)
    max_x = int(WINDOWWIDTH - (WINDOWWIDTH - 313) / 2 - 20)
    waves = [0.5]
    waves.extend(ALL_DATA)
    x_data = list(range(min_x, max_x, int((max_x-min_x)/WHOLE_IMAGE_WIDTH)))
    r = min(len(x_data), len(waves))
    for i in range(r):
        if waves[i] > 1:
            print("illegal wave %.2f"%waves[i])
        waves[i] = min(1, waves[i])
        waves[i] = max(0, waves[i])
        points.append((x_data[i], baseline + (1 - waves[i]) * 100))
    if len(points) > 0:
        linerect = pygame.draw.aalines(surface, (255, 255, 255), False, points, 5)
        linerect.topleft = (0, 0)
        pygame.display.flip()


def doCounting(windowSurface, seconds):
    clock = pygame.time.Clock()
    counter, text = seconds, str(seconds).rjust(3)
    num_font = pygame.font.Font("./fonts/TTTGB-Medium.ttf", 120)
    appleTipsFont = pygame.font.Font('./fonts/PingFang-Jian-ChangGuiTi-2.ttf', 30)
    game_explain = pygame.image.load('image/game_explaination.png')
    game_explain = pygame.transform.scale(game_explain, (280, 115))
    pygame.time.set_timer(pygame.USEREVENT, 1000)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.USEREVENT: 
                counter -= 1
                text = str(counter).rjust(3) if counter > 0 else "begin!"
            if e.type == QUIT:
                terminate()
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE: #escape quits
                    terminate()
        if counter <= 0:
            break
        else:
            windowSurface.fill((0, 0, 0))
            drawText(text, num_font, windowSurface, (WINDOWWIDTH / 2) - 145, (WINDOWHEIGHT / 3))
            drawText('左右摆动头部控制滑板', appleTipsFont, windowSurface, (WINDOWWIDTH / 2) - 150, (WINDOWHEIGHT / 2))
            windowSurface.blit(game_explain, (WINDOWWIDTH / 2 - 150, WINDOWHEIGHT / 2 + 60))
            windowSurface.blit(num_font.render(text, True, (0, 0, 0)), (32, 48))
            pygame.display.flip()
            clock.tick(60)
            continue
        break
    

def game():
    global playerRect, gameParams, count, connectUser, clientId, concenList, WINDOWHEIGHT, WINDOWWIDTH, IMAGE_WIDTH, max_x, x_data
    starttime = None  # for timing
    endtime = None
    # set up pygame, the window, and the mouse cursor
    pygame.init()

    mainClock = pygame.time.Clock()
    displayInfo = pygame.display.Info()
    # if displayInfo.current_h / WINDOWHEIGHT > displayInfo.current_w / WINDOWWIDTH:
    #     # fit width
    #     scale = displayInfo.current_w / WINDOWWIDTH
    #     WINDOWHEIGHT = int(scale * WINDOWHEIGHT)
    #     WINDOWWIDTH = displayInfo.current_w
    # else:
    #     # fit height
    #     scale = displayInfo.current_h / WINDOWHEIGHT
    #     WINDOWWIDTH = int(scale * WINDOWWIDTH)
    #     WINDOWHEIGHT = displayInfo.current_h
    max_x = WINDOWWIDTH - 35
    x_data = list(range(min_x, max_x, int((max_x-min_x)/IMAGE_WIDTH)))
    windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), pygame.FULLSCREEN)
    #windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('意念滑板赛')
    pygame.mouse.set_visible(False)

    # fonts
    font = pygame.font.Font("./fonts/TTTGB-Medium.ttf", 20)
    appleFont = pygame.font.Font("./fonts/TTTGB-Medium.ttf", 28)
    appleTipsFont = pygame.font.Font('./fonts/PingFang-Jian-ChangGuiTi-2.ttf', 14)
    appleTitleFont = pygame.font.Font('./fonts/PingFang-Jian-ChangGuiTi-2.ttf', 16)
    scoreFont = pygame.font.Font('./fonts/TTTGB-Medium.ttf', 12)

    # sounds
    pygame.mixer.init()
    gameOverSound = pygame.mixer.Sound('music/gameover.wav')
    pygame.mixer.music.load('music/technicolordreams.mp3')
    laugh = pygame.mixer.Sound('music/laugh.wav')
    reward = pygame.mixer.Sound('music/reward.wav')


    # images
    playerImage = pygame.image.load('image/skateboard.png')
    playerImage = pygame.transform.scale(playerImage, (int(60 * scale), int(70 * scale)))

    car2 = pygame.image.load('image/shit.png')
    # car3 = pygame.image.load('image/shoe2.png')
    # load the player avatar and nickname
    avatarImg, nickName = None, "匿名玩家"
    if connectUser:
        print(connectUser)
        avatarUrl = connectUser['avatar']
        avatarStr = urllib.request.urlopen(avatarUrl).read()
        avatarImg = pygame.image.load(io.BytesIO(avatarStr))
        nickName = connectUser['nickname']
    else:
        avatarImg = pygame.image.load('image/user_unlogin.png')
    avatarImg = pygame.transform.scale(avatarImg, (50, 50))

    playerRect = playerImage.get_rect()
    shoe1 = pygame.image.load('image/shoe1.png')
    shoe2 = pygame.image.load('image/shoe2.png')
    barriers = [car2]
    shoes = [shoe1, shoe2]
    background = pygame.image.load('image/game_bg.jpg')
    wavebg = pygame.image.load('image/wave_bg.png')
    wavebg = pygame.transform.scale(wavebg, (WINDOWWIDTH, 63))
    leftupBg = pygame.image.load('image/leftup_bg.png')
    leftupBg = pygame.transform.scale(leftupBg, (119, 63))
    rightupBg = pygame.image.load('image/rightup_bg.png')
    rightupBg = pygame.transform.scale(rightupBg, (62, 63))
    scoreBg = pygame.image.load('image/score_bg.png')
    scoreBg = pygame.transform.scale(scoreBg, (313, 431))
    scoreShoe = pygame.transform.scale(shoe2, (50, 50))

    # "Start" screen
    #drawText('Press any key', font, windowSurface, (WINDOWWIDTH / 3) - 30, (WINDOWHEIGHT / 3))
    #drawText('And Enjoy', font, windowSurface, (WINDOWWIDTH / 3), (WINDOWHEIGHT / 3)+30)
    #drawRect(windowSurface)
    #pygame.display.update()
    starttime = int(time.time())
    endtime = int(starttime + GAMEDURATION)
    #waitForPlayerToPressKey()
    zero=0
    if not os.path.exists("data/save.dat"):
        f=open("data/save.dat",'w')
        f.write(str(zero))
        f.close()   
    v=open("data/save.dat",'r')
    topScore = int(v.readline())
    v.close()
    pygame.mixer.music.play(-1, 0.0)

    doCounting(windowSurface, 5)

    while (count>0):
        # start of the game
        baddies = []
        stars = []
        walls = []
        score = 0
        playerRect.topleft = ((WINDOWWIDTH - playerRect.width) / 2, WINDOWHEIGHT - playerRect.height)
        moveLeft = moveRight = moveUp = moveDown = False
        reverseCheat = slowCheat = False
        baddieAddCounter = 0
        starAddCounter = 0        

        while True: # the game loop

            for event in pygame.event.get():
                
                if event.type == QUIT:
                    terminate()

                if event.type == KEYDOWN:
                    if event.key == ord('z'):
                        reverseCheat = True
                    if event.key == ord('x'):
                        slowCheat = True
                    if event.key == K_LEFT or event.key == ord('a'):
                        moveRight = False
                        moveLeft = True
                    if event.key == K_RIGHT or event.key == ord('d'):
                        moveLeft = False
                        moveRight = True
                    if event.key == K_UP or event.key == ord('w'):
                        moveDown = False
                        moveUp = True
                    if event.key == K_DOWN or event.key == ord('s'):
                        moveUp = False
                        moveDown = True

                if event.type == KEYUP:
                    if event.key == ord('z'):
                        reverseCheat = False
                        score = 0
                    if event.key == ord('x'):
                        slowCheat = False
                        score = 0
                    if event.key == K_ESCAPE:
                        terminate()
                

                    if event.key == K_LEFT or event.key == ord('a'):
                        moveLeft = False
                    if event.key == K_RIGHT or event.key == ord('d'):
                        moveRight = False
                    if event.key == K_UP or event.key == ord('w'):
                        moveUp = False
                    if event.key == K_DOWN or event.key == ord('s'):
                        moveDown = False
                

            # Add new baddies at the top of the screen
            if not reverseCheat and not slowCheat:
                baddieAddCounter += 1
                starAddCounter += 1
                
            if baddieAddCounter == gameParams['addNewBaddieRate']:
                baddieAddCounter = 0
                baddieSize = int(54 * scale)
                newBaddie = {'rect': pygame.Rect(random.randint(int(55 * scale), WINDOWWIDTH - int(55 * scale) - baddieSize), 0, int(56 * scale), int(62 * scale)),
                            'speed': BADDIESPEED,
                            'surface':pygame.transform.scale(random.choice(barriers), (int(56 * scale), int(62 * scale))),
                            }
                baddies.append(newBaddie)

            if starAddCounter == gameParams['addNewStarRate']:
                starAddCounter = 0
                starSize = int(67 * scale)
                newStar = {'rect': pygame.Rect(random.randint(int(55 * scale), WINDOWWIDTH - int(55 * scale) - starSize), 0, starSize, starSize),
                            'speed': BADDIESPEED,
                            'surface':pygame.transform.scale(random.choice(shoes), (starSize, starSize)),
                            }
                stars.append(newStar)

            background_wall = {'rect': pygame.Rect(0, 0, WINDOWWIDTH, WINDOWHEIGHT),
                    'speed': BADDIESPEED,
                    'surface':pygame.transform.scale(background, (WINDOWWIDTH, WINDOWHEIGHT)),
                    }
                
            # Move the player around.
            if moveLeft and playerRect.left > PLAYER_MIN_X:
                playerRect.move_ip(-1 * PLAYERMOVERATE, 0)
            if moveRight and playerRect.right < PLAYER_MAX_X:
                playerRect.move_ip(PLAYERMOVERATE, 0)
            if moveUp and playerRect.top > 0:
                playerRect.move_ip(0, -1 * PLAYERMOVERATE)
            if moveDown and playerRect.bottom < WINDOWHEIGHT:
                playerRect.move_ip(0, PLAYERMOVERATE)
            
            for b in baddies:
                if not reverseCheat and not slowCheat:
                    b['rect'].move_ip(0, BADDIESPEED)
                elif reverseCheat:
                    b['rect'].move_ip(0, -5)
                elif slowCheat:
                    b['rect'].move_ip(0, 1)

            for s in stars:
                if not reverseCheat and not slowCheat:
                    s['rect'].move_ip(0, BADDIESPEED)
                elif reverseCheat:
                    s['rect'].move_ip(0, -5)
                elif slowCheat:
                    s['rect'].move_ip(0, 1)

            for b in baddies:
                if b['rect'].top > WINDOWHEIGHT:
                    baddies.remove(b)

            for s in stars:
                if s['rect'].top > WINDOWHEIGHT:
                    stars.remove(s)

            # Draw the game world on the window.
            # windowSurface.fill(BACKGROUNDCOLOR)

            # Draw the score and top score.            
            # drawText('Score: %s' % (score), font, windowSurface, 310, 0)
            curtime = int(time.time())
            if (endtime - curtime <= 0):
                # time up
                # upload the scroe
                t = threading.Thread(target=uploadScore, args=(score,concenList))
                t.start()
                break
            # else:
            #     drawText('Time Elapse: %s' % (endtime - curtime), font, windowSurface,310, 20)
            # drawText('Top Score: %s' % (topScore), font, windowSurface,310, 40)
            # drawText('Rest Life: %s' % (count), font, windowSurface, 310, 60)
            # drawText('Speed: %s' % (gameParams['speed']), font, windowSurface, 310, 80)    
            windowSurface.blit(background_wall['surface'], background_wall['rect'])

            windowSurface.blit(playerImage, playerRect)
            
            for b in baddies:
                windowSurface.blit(b['surface'], b['rect'])
            
            for s in stars:
                windowSurface.blit(s['surface'], s['rect'])                

            windowSurface.blit(wavebg, (0, 30))
            windowSurface.blit(leftupBg, (10, 30))
            windowSurface.blit(scoreShoe, (13, 35))
            drawText('X %d'%score, font, windowSurface, 66, 54)
            windowSurface.blit(rightupBg, (WINDOWWIDTH - 72, 30))
            drawText('%d'%(endtime - curtime), font, windowSurface, WINDOWWIDTH - 50, 54)
            # windowSurface.blit(avatarImg, (10, 10))
            # drawText(nickName, font, windowSurface, 10, 65)              

            pygame.display.update()

            # Check if any of the baddie have hit the player.
            if playerHasHitBaddie(playerRect, baddies):
                gameOverSound.play()
                if score > topScore:
                    g=open("data/save.dat",'w')
                    g.write(str(score))
                    g.close()
                    topScore = score
                # upload the score
                t = threading.Thread(target=uploadScore, args=(score, concenList))
                t.start()
                break

            # Check if any of the star have hit the player.
            if playerHasHitStar(playerRect, stars):
                reward.play()
                score += 1

            # Update brain wave image
            #t = threading.Thread(target=drawLines, args=(windowSurface, x_data, gameParams['beta']))
            #t.start()
            drawLines(windowSurface, x_data, gameParams['beta'])

            mainClock.tick(FPS)

        # "Game Over" screen.
        #pygame.mixer.music.stop()
        count=count-1        
        time.sleep(1)
        maskSurface = windowSurface.convert_alpha() #important, can not fill directly
        maskSurface.fill(MASKCOLOR)
        windowSurface.blit(maskSurface, (0, 0))
        sampleAllData() # 对ALL_DATA进行等间隔抽稀，只留下60个采样
        baseline = WINDOWHEIGHT / 2 - 300
        drawText('游戏结束，可在小程序查看分享', appleTipsFont, windowSurface, (WINDOWWIDTH - 190) / 2, baseline)
        drawText('你的游戏记录', appleTipsFont, windowSurface, (WINDOWWIDTH - 90) / 2, baseline + 25)
        windowSurface.blit(scoreBg, ((WINDOWWIDTH - 313) / 2, baseline + 67))
        drawText('---  本局脑波图  ---', appleTitleFont, windowSurface, (WINDOWWIDTH - 160) / 2, baseline + 82)
        windowSurface.blit(avatarImg, ((WINDOWWIDTH - 50) / 2, baseline + 117))
        typeId = min(score, 100) / 20 + 1
        if score >= 100:
            typeId = 6
        typeImg = pygame.image.load('./image/type%d.png'%typeId)
        typeImg = pygame.transform.scale(typeImg, (130, 24))
        windowSurface.blit(typeImg, ((WINDOWWIDTH - 130) / 2, baseline + 187))
        avgConcen = 80
        print(concenList)
        if len(concenList) > 0:
            avgConcen = sum(concenList) / len(concenList)
            avgConcen = min(avgConcen, 100)
        drawText("游戏得分: %d分  专注度: %d分"%(score, avgConcen), scoreFont, windowSurface, WINDOWWIDTH / 2 - 85, baseline + 222)
        windowSurface.fill(WHITECOLOR, (((WINDOWWIDTH - 288) / 2, baseline + 472), (288, 50)))
        drawText('按任意键再玩一次', appleFont, windowSurface, int((WINDOWWIDTH - 232) / 2), baseline + 482, (102, 143, 15))
        drawText('退出(ESC)', appleFont, windowSurface, int((WINDOWWIDTH - 105) / 2), baseline + 547)
        drawWholeLines(windowSurface, baseline + 267)
        pygame.display.update()
        time.sleep(2)
        waitForPlayerToPressKey()
        starttime = int(time.time())
        endtime = int(starttime + GAMEDURATION)      
        score = 0
        concenList = []
    terminate()

def loop_event():
    global gameParams, playerRect, BADDIESPEED, PLAYERMOVERATE, PLAYER_MIN_X, PLAYER_MAX_X, concenList
    while True:
        event.wait()
        # 更新数据
        if playerRect is not None:
            BADDIESPEED = gameParams['speed']
            concenList.append(gameParams['concen'])
            playerRect.left = gameParams['left']
            if playerRect.left < PLAYER_MIN_X:
                playerRect.left = PLAYER_MIN_X
            if playerRect.right > PLAYER_MAX_X:
                playerRect.right = PLAYER_MAX_X
        event.clear()

def main(user=None, cid=None, callback=None):
    global gameParams, oscProcess, connectUser, clientId, returnCallback, IMAGE_WIDTH, concenList
    gameParams = multiprocessing.Manager().dict()
    gameParams['speed'] = 8
    gameParams['left'] = WINDOWWIDTH/2
    gameParams['acc'] = 0
    gameParams['beta'] = [0] * IMAGE_WIDTH
    gameParams['addNewBaddieRate'] = MINADDNEWBADDIERATE
    gameParams['addNewStarRate'] = MINADDNEWSTARRATE
    gameParams['concen'] = []

    concenList = []

    connectUser = user
    clientId = cid
    returnCallback = callback
    
    thread.start_new_thread(loop_event, ())
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="192.168.8.119",
                        help="The ip to listen on")
    parser.add_argument("--port",
                        type=int,
                        default=5001,
                        help="The port to listen on")
    args = parser.parse_args()
    print('ip=%s, port=%d'%(args.ip, args.port))
    oscProcess = multiprocessing.Process(target=start_osc, args=(args.ip, args.port, gameParams))
    oscProcess.start()

    game()    

if __name__ == '__main__':
    main()
