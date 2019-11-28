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

event = multiprocessing.Event()

WINDOWWIDTH = 450
WINDOWHEIGHT = 800
TEXTCOLOR = (255, 255, 255)
BACKGROUNDCOLOR = (0, 0, 0)
FPS = 60
BADDIEMINSIZE = 10
BADDIEMAXSIZE = 40
BADDIESPEED = 8
#MARGINLEFT = 54
#MARGINRIGHT = 340
MINADDNEWBADDIERATE = 107
MAXADDNEWBADDIERATE = 87
MINADDNEWSTARRATE = 20
MAXADDNEWSTARRATE = 10
INITPLAYERMOVERATE = 5
PLAYERMOVERATE = 5
GAMEDURATION = 60 # game duration

count=3

# for muse tracking
playerRect = None
gameParams = None
oscProcess = None

MINY = -0.5
MAXY = 1

connectUser = None
clientId = None
returnCallback = None

PLAYER_MIN_X = 55
PLAYER_MAX_X = 395

def concen_handler(unused_addr, args, value):
    #speed = args[0]['speed']
    #print(value)
    #speed = int(((value + 20) / 100) * 20)
    speed = value * 20
    if speed < 8:
        speed = 8
    if speed > 20:
        speed = 20
    print(speed)
    args[0]['speed'] = speed
    event.set()
    
def acc_handler(unused_addr, args, x, y, z):
    # normalize y
    global WINDOWWIDTH
    #left = args[0]['left']
    rate = (y - MINY) / (MAXY - MINY)
    if rate > 1:
        rate = 1
    if rate < 0:
        rate = 0
    x = WINDOWWIDTH * rate
    args[0]['left'] = PLAYER_MIN_X + x
    event.set()

def start_osc(ip, port, info):
    dispatcher = dsp.Dispatcher()
    #dispatcher.map("/muse/algorithm/concentration", concen_handler, info)
    dispatcher.map("/muse/elements/beta_absolute", concen_handler, info)
    dispatcher.map("/muse/acc", acc_handler, info)

    server = osc_server.ThreadingOSCUDPServer(
        (ip, port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()    

def terminate():
    global oscProcess, clientId, connectUser, returnCallback
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
    # go back the startup page
    if returnCallback:
        returnCallback()
    else:
        sys.exit()

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

def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, TEXTCOLOR)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def uploadScore(score):
    global clientId, connectUser
    if clientId != None and connectUser != None:
        response = urllib.request.urlopen('https://forrestlin.cn/games/finishGame/%s/%s/%d'%(clientId, connectUser['userId'], score))
        res = response.read().decode('utf-8')
        resJson = json.loads(res)
        if not resJson['success']:
            print('Failed to upload score, reason: %s'%resJson['errMsg'])
        else:
            print('Succeed to upload score')

def game():
    global playerRect, gameParams, count, connectUser, clientId
    starttime = None  # for timing
    endtime = None
    # set up pygame, the window, and the mouse cursor
    pygame.init()
    mainClock = pygame.time.Clock()
    windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('意念滑板赛')
    pygame.mouse.set_visible(False)

    # fonts
    font = pygame.font.Font("./fonts/TTTGB-Medium.ttf", 20)
    appleFont = pygame.font.Font("./fonts/PingFang-Jian-ChangGuiTi-2.ttf", 30)

    # sounds
    gameOverSound = pygame.mixer.Sound('music/crash.wav')
    pygame.mixer.music.load('music/skate1.mp3')
    laugh = pygame.mixer.Sound('music/laugh.wav')


    # images
    playerImage = pygame.image.load('image/skateboard.png')
    playerImage = pygame.transform.scale(playerImage, (94, 82))

    car2 = pygame.image.load('image/shit.png')
    # car3 = pygame.image.load('image/shoe2.png')
    # load the player avatar and nickname
    # avatarImg, nickName = None, "匿名玩家"
    # if connectUser:
    #     print(connectUser)
    #     avatarUrl = connectUser['avatar']
    #     avatarStr = urllib.request.urlopen(avatarUrl).read()
    #     avatarImg = pygame.image.load(io.BytesIO(avatarStr))
    #     avatarImg = pygame.transform.scale(avatarImg, (50, 50))
    #     nickName = connectUser['nickname']
    # else:
    #     avatarImg = pygame.image.load('image/user_unlogin.png')

    playerRect = playerImage.get_rect()        
    shoe1 = pygame.image.load('image/shoe1.png')
    shoe2 = pygame.image.load('image/shoe2.png')
    barriers = [car2]
    shoes = [shoe1, shoe2]
    background = pygame.image.load('image/game_bg.jpg')
    leftupBg = pygame.image.load('image/leftup_bg.png')
    leftupBg = pygame.transform.scale(leftupBg, (119, 63))
    rightupBg = pygame.image.load('image/rightup_bg.png')
    rightupBg = pygame.transform.scale(rightupBg, (62, 63))
    scoreBg = pygame.image.load('image/score_bg.png')
    scoreBg = pygame.transform.scale(scoreBg, (313, 431))
    scoreShoe = pygame.transform.scale(shoe2, (50, 50))

    # "Start" screen
    drawText('Press any key', font, windowSurface, (WINDOWWIDTH / 3) - 30, (WINDOWHEIGHT / 3))
    drawText('And Enjoy', font, windowSurface, (WINDOWWIDTH / 3), (WINDOWHEIGHT / 3)+30)
    pygame.display.update()
    starttime = int(time.time())
    endtime = int(starttime + GAMEDURATION)
    waitForPlayerToPressKey()
    zero=0
    if not os.path.exists("data/save.dat"):
        f=open("data/save.dat",'w')
        f.write(str(zero))
        f.close()   
    v=open("data/save.dat",'r')
    topScore = int(v.readline())
    v.close()
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
        #pygame.mixer.music.play(-1, 0.0)

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
                baddieSize = 54
                newBaddie = {'rect': pygame.Rect(random.randint(55, 395 - baddieSize), 0, 56, 60),
                            'speed': BADDIESPEED,
                            'surface':pygame.transform.scale(random.choice(barriers), (56, 60)),
                            }
                baddies.append(newBaddie)

            if starAddCounter == gameParams['addNewStarRate']:
                starAddCounter = 0
                starSize = 67
                newStar = {'rect': pygame.Rect(random.randint(55, 395 - starSize), 0, 67, 67),
                            'speed': BADDIESPEED,
                            'surface':pygame.transform.scale(random.choice(shoes), (67, 67)),
                            }
                stars.append(newStar)

            # sideLeft= {'rect': pygame.Rect(0,0,303,600),
            #         'speed': BADDIESPEED,
            #         'surface':pygame.transform.scale(wallLeft, (303, 599)),
            #         }
            # sideRight= {'rect': pygame.Rect(674,0,303,600),
            #         'speed': BADDIESPEED,
            #         'surface':pygame.transform.scale(wallRight, (303, 599)),
            #         }
            # walls.append(sideLeft)
            # walls.append(sideRight)
            background_wall = {'rect': pygame.Rect(0, 0, WINDOWWIDTH, WINDOWHEIGHT),
                    'speed': BADDIESPEED,
                    'surface':pygame.transform.scale(background, (WINDOWWIDTH, WINDOWHEIGHT)),
                    }
            walls.append(background_wall)
                

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

            # for s in walls:
            #     if not reverseCheat and not slowCheat:
            #         s['rect'].move_ip(0, BADDIESPEED)
            #     elif reverseCheat:
            #         s['rect'].move_ip(0, -5)
            #     elif slowCheat:
            #         s['rect'].move_ip(0, 1)                    

            for b in baddies:
                if b['rect'].top > WINDOWHEIGHT:
                    baddies.remove(b)

            for s in stars:
                if s['rect'].top > WINDOWHEIGHT:
                    stars.remove(s)

            for s in walls:
                if s['rect'].top > WINDOWHEIGHT:
                    walls.remove(s)

            # Draw the game world on the window.
            # windowSurface.fill(BACKGROUNDCOLOR)

            # Draw the score and top score.            
            # drawText('Score: %s' % (score), font, windowSurface, 310, 0)
            curtime = int(time.time())
            if (endtime - curtime <= 0):
                break
            # else:
            #     drawText('Time Elapse: %s' % (endtime - curtime), font, windowSurface,310, 20)
            # drawText('Top Score: %s' % (topScore), font, windowSurface,310, 40)
            # drawText('Rest Life: %s' % (count), font, windowSurface, 310, 60)
            # drawText('Speed: %s' % (gameParams['speed']), font, windowSurface, 310, 80)    
            for s in walls:
                windowSurface.blit(s['surface'], s['rect'])

            windowSurface.blit(playerImage, playerRect)
            
            for b in baddies:
                windowSurface.blit(b['surface'], b['rect'])
            
            for s in stars:
                windowSurface.blit(s['surface'], s['rect'])                

            windowSurface.blit(leftupBg, (0, 0))
            windowSurface.blit(scoreShoe, (3, 5))
            drawText('X %d'%score, font, windowSurface, 56, 24)
            windowSurface.blit(rightupBg, (WINDOWWIDTH - 62, 0))
            drawText('%d'%(endtime - curtime), font, windowSurface, WINDOWWIDTH - 40, 24)
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
                gameOverSound.stop()
                # upload the scroe
                t = threading.Thread(target=uploadScore, args=(score,))
                t.start()
                break

            # Check if any of the star have hit the player.
            if playerHasHitStar(playerRect, stars):
                score += 1

            mainClock.tick(FPS)

        # "Game Over" screen.
        #pygame.mixer.music.stop()
        count=count-1        
        time.sleep(1)
        if (count==0):
            laugh.play()
        drawText('Game over', font, windowSurface, (WINDOWWIDTH / 3), (WINDOWHEIGHT / 3))
        drawText('Press any key to play again.', font, windowSurface, (WINDOWWIDTH / 3) - 80, (WINDOWHEIGHT / 3) + 30)
        pygame.display.update()
        time.sleep(2)
        waitForPlayerToPressKey()
        starttime = int(time.time())
        endtime = int(starttime + GAMEDURATION)
        count=3        

def loop_event():
    global gameParams, playerRect, BADDIESPEED, PLAYERMOVERATE, PLAYER_MIN_X, PLAYER_MAX_X
    while True:
        event.wait()
        # 更新数据
        if playerRect is not None:
            BADDIESPEED = gameParams['speed']
            playerRect.left = gameParams['left']            
            if playerRect.left < PLAYER_MIN_X:
                playerRect.left = PLAYER_MIN_X
            if playerRect.right > PLAYER_MAX_X:
                playerRect.right = PLAYER_MAX_X
        event.clear()

def main(user=None, cid=None, callback=None):
    global gameParams, oscProcess, connectUser, clientId, returnCallback
    gameParams = multiprocessing.Manager().dict()
    gameParams['speed'] = 8
    gameParams['left'] = WINDOWWIDTH/2
    gameParams['acc'] = 0
    gameParams['addNewBaddieRate'] = MINADDNEWBADDIERATE
    gameParams['addNewStarRate'] = MINADDNEWSTARRATE

    connectUser = user
    clientId = cid
    returnCallback = callback
    
    thread.start_new_thread(loop_event, ())
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1",
                        help="The ip to listen on")
    parser.add_argument("--port",
                        type=int,
                        default=5000,
                        help="The port to listen on")
    args = parser.parse_args()
    
    oscProcess = multiprocessing.Process(target=start_osc, args=(args.ip, args.port, gameParams))
    oscProcess.start()

    game()    

if __name__ == '__main__':
    main()