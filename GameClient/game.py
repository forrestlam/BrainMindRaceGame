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

event = multiprocessing.Event()

WINDOWWIDTH = 1000
WINDOWHEIGHT = 600
TEXTCOLOR = (255, 255, 255)
BACKGROUNDCOLOR = (0, 0, 0)
FPS = 60
BADDIEMINSIZE = 10
BADDIEMAXSIZE = 40
BADDIESPEED = 8
MARGINLEFT = 310
MARGINRIGHT = 640
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

def concen_handler(unused_addr, args, value):
    speed = args[0]['speed']
    speed = int((value / 100) * 20)
    if speed < 1:
        speed = 1
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
    x = 380 * rate
    args[0]['left'] = 310 + x
    event.set()

def start_osc(ip, port, info):
    dispatcher = dsp.Dispatcher()
    dispatcher.map("/muse/algorithm/concentration", concen_handler, info)
    dispatcher.map("/muse/acc", acc_handler, info)

    server = osc_server.ThreadingOSCUDPServer(
        (ip, port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()    

def terminate():
    global oscProcess
    pygame.quit()
    oscProcess.terminate()
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
            print('Failed to upload score')

def game():
    global playerRect, gameParams, count, connectUser, clientId
    starttime = None  # for timing
    endtime = None
    # set up pygame, the window, and the mouse cursor
    pygame.init()
    mainClock = pygame.time.Clock()
    windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('car race')
    pygame.mouse.set_visible(False)

    # fonts
    font = pygame.font.SysFont(None, 30)

    # sounds
    gameOverSound = pygame.mixer.Sound('music/crash.wav')
    pygame.mixer.music.load('music/skate1.mp3')
    laugh = pygame.mixer.Sound('music/laugh.wav')


    # images
    playerImage = pygame.image.load('image/skateboard.png')

    car2 = pygame.image.load('image/car2.png')
    car3 = pygame.image.load('image/car3.png')
    car4 = pygame.image.load('image/car4.png')
    # load the player avatar and nickname
    avatarImg, nickName = None, "匿名玩家"
    if connectUser:
        print(connectUser)
        avatarUrl = connectUser['avatar']
        avatarStr = urllib.request.urlopen(avatarUrl).read()
        avatarImg = pygame.image.load(io.BytesIO(avatarStr))
        avatarImg = pygame.transform.scale(avatarImg, (50, 50))
        nickName = connectUser['nickname']
    else:
        avatarImg = pygame.image.load('image/user_unlogin.png')

    playerRect = playerImage.get_rect()        
    starImage = pygame.image.load('image/star.png')
    sample = [car3, car4, car2]
    wallLeft = pygame.image.load('image/left.png')
    wallRight = pygame.image.load('image/right.png')
    MARGINLEFT = wallLeft.get_rect().width
    MARGINRIGHT = WINDOWWIDTH - wallRight.get_rect().width - playerRect.width

    # "Start" screen
    drawText('Press any key to start the game.', font, windowSurface, (WINDOWWIDTH / 3) - 30, (WINDOWHEIGHT / 3))
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
        playerRect.topleft = (WINDOWWIDTH / 2, WINDOWHEIGHT - playerRect.height)
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
                baddieSize = 30
                newBaddie = {'rect': pygame.Rect(random.randint(317, 650), 0 - baddieSize, 23, 47),
                            'speed': BADDIESPEED,
                            'surface':pygame.transform.scale(random.choice(sample), (23, 47)),
                            }
                baddies.append(newBaddie)

            if starAddCounter == gameParams['addNewStarRate']:
                starAddCounter = 0
                newStar = {'rect': pygame.Rect(random.randint(317, 650), 0 - 40, 40, 40),
                            'speed': BADDIESPEED,
                            'surface':pygame.transform.scale(starImage, (40, 40)),
                            }
                stars.append(newStar)

            sideLeft= {'rect': pygame.Rect(0,0,303,600),
                    'speed': BADDIESPEED,
                    'surface':pygame.transform.scale(wallLeft, (303, 599)),
                    }
            sideRight= {'rect': pygame.Rect(674,0,303,600),
                    'speed': BADDIESPEED,
                    'surface':pygame.transform.scale(wallRight, (303, 599)),
                    }
            walls.append(sideLeft)
            walls.append(sideRight)
                

            # Move the player around.
            if moveLeft and playerRect.left > 0:
                playerRect.move_ip(-1 * PLAYERMOVERATE, 0)
            if moveRight and playerRect.right < WINDOWWIDTH:
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

            for s in walls:
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

            for s in walls:
                if s['rect'].top > WINDOWHEIGHT:
                    walls.remove(s)

            # Draw the game world on the window.
            windowSurface.fill(BACKGROUNDCOLOR)

            # Draw the score and top score.            
            drawText('Score: %s' % (score), font, windowSurface, 310, 0)
            curtime = int(time.time())
            if (endtime - curtime <= 0):
                break
            else:
                drawText('Time Elapse: %s' % (endtime - curtime), font, windowSurface,310, 20)
            drawText('Top Score: %s' % (topScore), font, windowSurface,310, 40)
            drawText('Rest Life: %s' % (count), font, windowSurface, 310, 60)
            drawText('Speed: %s' % (gameParams['speed']), font, windowSurface, 310, 80)            
            windowSurface.blit(playerImage, playerRect)
            
            for b in baddies:
                windowSurface.blit(b['surface'], b['rect'])
            
            for s in stars:
                windowSurface.blit(s['surface'], s['rect'])                

            for s in walls:
                windowSurface.blit(s['surface'], s['rect'])  

            windowSurface.blit(avatarImg, (10, 10))
            drawText(nickName, font, windowSurface, 10, 65)              

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
                uploadScore(score)
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
    global gameParams, playerRect, BADDIESPEED, PLAYERMOVERATE
    while True:
        event.wait()
        # 更新数据
        if playerRect is not None:
            BADDIESPEED = gameParams['speed']
            playerRect.left = gameParams['left']            
            if playerRect.left < MARGINLEFT:
                playerRect.left = MARGINLEFT
            if playerRect.left > MARGINRIGHT:
                playerRect.left = MARGINRIGHT
        event.clear()

def main(user=None, cid=None):
    global gameParams, oscProcess, connectUser, clientId
    gameParams = multiprocessing.Manager().dict()
    gameParams['speed'] = 8
    gameParams['left'] = WINDOWWIDTH/2
    gameParams['acc'] = 0
    gameParams['addNewBaddieRate'] = MINADDNEWBADDIERATE
    gameParams['addNewStarRate'] = MINADDNEWSTARRATE

    connectUser = user
    clientId = cid
    
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