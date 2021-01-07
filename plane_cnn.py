# -*- coding: utf-8 -*-
import pygame
from sys import exit
from pygame.locals import *
import random
import cv2
from imutils import resize
from paddlex.deploy import Predictor
import pygame.font
import os


def text_objects(text, font):
    # 将字符串转换为pygame的文本框
    textSurface = font.render(text, True, (0, 0, 0))
    return textSurface, textSurface.get_rect()


# 设置游戏屏幕大小
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800

# 手势识别器
model = Predictor('rec_inference_model', use_gpu=True)

# 子弹类


class Bullet(pygame.sprite.Sprite):
    def __init__(self, bullet_img, init_pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img  # 子弹图像
        self.rect = self.image.get_rect()  # 子弹大小和位置
        self.rect.midbottom = init_pos  # 设置初始位置
        self.speed = 10  # 子弹速度

    def move(self):
        self.rect.top -= self.speed  # 子弹移动

# 玩家飞机类


class Player(pygame.sprite.Sprite):
    def __init__(self, plane_img, player_rect, init_pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = []                                 # 用来存储玩家飞机图片的列表
        for i in range(len(player_rect)):
            self.image.append(plane_img.subsurface(
                player_rect[i]).convert_alpha())
        self.rect = player_rect[0]                      # 初始化图片所在的矩形
        self.rect.topleft = init_pos                    # 初始化矩形的左上角坐标
        self.speed = 8                                  # 初始化玩家飞机速度，这里是一个确定的值
        self.bullets = pygame.sprite.Group()            # 玩家飞机所发射的子弹的集合
        self.is_hit = False                             # 玩家是否被击中

    # 发射子弹
    def shoot(self, bullet_img):
        bullet = Bullet(bullet_img, self.rect.midtop)
        self.bullets.add(bullet)

    # 向上移动，需要判断边界
    def moveUp(self):
        if self.rect.top <= 0:
            self.rect.top = 0
        else:
            self.rect.top -= self.speed

    # 向下移动，需要判断边界
    def moveDown(self):
        if self.rect.top >= SCREEN_HEIGHT - self.rect.height:
            self.rect.top = SCREEN_HEIGHT - self.rect.height
        else:
            self.rect.top += self.speed

    # 向左移动，需要判断边界
    def moveLeft(self):
        if self.rect.left <= 0:
            self.rect.left = 0
        else:
            self.rect.left -= self.speed

    # 向右移动，需要判断边界
    def moveRight(self):
        if self.rect.left >= SCREEN_WIDTH - self.rect.width:
            self.rect.left = SCREEN_WIDTH - self.rect.width
        else:
            self.rect.left += self.speed

# 敌机类


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_img, enemy_down_imgs, init_pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.topleft = init_pos
        self.down_imgs = enemy_down_imgs
        self.speed = 1

    # 敌机移动，边界判断及删除在游戏主循环里处理
    def move(self):
        self.rect.top += self.speed


# 初始化 pygame
pygame.init()

# 设置游戏界面大小、背景图片及标题
# 游戏界面像素大小
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# 游戏界面标题
pygame.display.set_caption('Python打飞机大战')

# 背景图
background = pygame.image.load('resources/image/background.png').convert()

# 开始游戏
# start_btn = pygame.image.load("2019031114200572.png").convert()

# Game Over 的背景图
game_over = pygame.image.load('resources/image/gameover.png')

# 飞机及子弹图片集合
plane_img = pygame.image.load('resources/image/shoot.png')

# 设置玩家飞机不同状态的图片列表，多张图片展示为动画效果
player_rect = []
player_rect.append(pygame.Rect(0, 99, 102, 126))        # 玩家飞机图片
player_rect.append(pygame.Rect(165, 234, 102, 126))     # 玩家爆炸图片

player_pos = [200, 600]
player = Player(plane_img, player_rect, player_pos)

# 子弹图片
bullet_rect = pygame.Rect(1004, 987, 9, 21)
bullet_img = plane_img.subsurface(bullet_rect)

# 敌机不同状态的图片列表，包括正常敌机，爆炸的敌机图片
enemy1_rect = pygame.Rect(534, 612, 57, 43)
enemy1_img = plane_img.subsurface(enemy1_rect)
enemy1_down_imgs = plane_img.subsurface(pygame.Rect(267, 347, 57, 43))


# 存储敌机，管理多个对象
enemies1 = pygame.sprite.Group()

# 存储被击毁的飞机
enemies_down = pygame.sprite.Group()

# 初始化射击及敌机移动频率
shoot_frequency = 0
enemy_frequency = 0

# 初始化分数
score = 0

# 游戏循环帧率设置
clock = pygame.time.Clock()

# 判断游戏循环退出的参数
running = True

# 移动方向（初始化）
move = 'pause'

# 读取前置摄像头
camera = cv2.VideoCapture(0)

# 手势区域
top, right, bottom, left = 90, 360, 285, 580

fps = 50

start = False

if os.path.exists('data.txt'):
    with open('data.txt', 'r') as f:
        max_score = eval(f.read())
else:
    max_score = 0

# 游戏主循环
while running:
    # 控制游戏最大帧率
    clock.tick(fps)
    # 绘制背景
    screen.fill(0)
    screen.blit(background, (0, 0))

    # 绘制玩家飞机
    if not player.is_hit:
        screen.blit(player.image[0], player.rect)  # 将正常飞机画出来
    else:
        # 玩家飞机被击中后的效果处理
        screen.blit(player.image[1], player.rect)  # 将爆炸的飞机画出来
        running = False

    if not start:
        # 开始界面
        screen_rect = screen.get_rect()
        largeText = pygame.font.Font('platech.ttf', 80)
        TextSurf, TextRect = text_objects('飞机大战', largeText)
        TextRect.center = ((SCREEN_WIDTH/2), (SCREEN_HEIGHT/3))
        screen.blit(TextSurf, TextRect)  # 绘制“飞机大战”文本框

        # 设置按钮的尺寸和其他属性
        width, height = 200, 50
        button_color = (0, 255, 0)
        text_color = (255, 255, 255)
        font = pygame.font.SysFont(None, 48)

        # 创建按钮的rect对象，居中
        rect = pygame.Rect(0, 0, width, height)
        rect.center = screen_rect.center
        msg_image = font.render("Play", True, text_color,
                                button_color)
        msg_image_rect = msg_image.get_rect()
        msg_image_rect.center = rect.center
        screen.fill(button_color, rect)
        screen.blit(msg_image, msg_image_rect)
        pressed = pygame.mouse.get_pressed()  # 创建开始游戏按钮
        x1, y1 = pygame.mouse.get_pos()
        if x1 > 142 and y1 > 377:
            if x1 < 338 and y1 < 423:
                if pressed[0]:
                    # 响应点击Play事件，游戏开始
                    start = True

    else:
        if score < 25:
            # 生成子弹，需要控制发射频率
            # 首先判断玩家飞机没有被击中
            if not player.is_hit:
                if shoot_frequency % 15 == 0:
                    # 循环15次发射一个子弹
                    player.shoot(bullet_img)
                if shoot_frequency % 5 == 0:
                    # 读取摄像头图像
                    grabbed, frame = camera.read()
                    if not grabbed:
                        break
                    frame = resize(frame, width=600)  # 对摄像头图像放缩
                    frame = cv2.flip(frame, 1)  # 图像镜像处理（左右手问题）
                    cv2.rectangle(frame, (left, top),
                                  (right, bottom), (0, 255, 0), 2)  # 绘制绿框
                    roi = frame[top:bottom, right:left]  # 手势位置
                    if shoot_frequency % 10 == 0:
                        pred = model.predict(roi)  # 使用SVM/CNN预测手势
                        move = pred[0]['category']
                        print('-[INFO] Update movement to ', move)
                    cv2.imshow('frame', frame)  # 显示摄像头画面
                    cv2.waitKey(int(1000/fps))
                shoot_frequency += 1
                if shoot_frequency >= 15:
                    shoot_frequency = 0

            # 生成敌机，需要控制生成频率
            # 循环50次生成一架敌机
            if enemy_frequency % 50 == 0:
                enemy1_pos = [random.randint(
                    0, SCREEN_WIDTH - enemy1_rect.width), 0]
                enemy1 = Enemy(enemy1_img, enemy1_down_imgs, enemy1_pos)
                enemies1.add(enemy1)
            enemy_frequency += 1
            if enemy_frequency >= 100:
                enemy_frequency = 0

            for bullet in player.bullets:
                # 以固定速度移动子弹
                bullet.move()
                # 移动出屏幕后删除子弹
                if bullet.rect.bottom < 0:
                    player.bullets.remove(bullet)

            for enemy in enemies1:
                # 2. 移动敌机
                enemy.move()
                # 3. 敌机与玩家飞机碰撞效果处理
                if pygame.sprite.collide_circle(enemy, player):
                    enemies_down.add(enemy)
                    enemies1.remove(enemy)
                    player.is_hit = True
                    break
                # 4. 移动出屏幕后删除敌人
                if enemy.rect.top < 0:
                    enemies1.remove(enemy)

            # 敌机被子弹击中效果处理
            # 将被击中的敌机对象添加到击毁敌机 Group 中
            enemies1_down = pygame.sprite.groupcollide(
                enemies1, player.bullets, 1, 1)
            for enemy_down in enemies1_down:
                enemies_down.add(enemy_down)

            # 敌机被子弹击中效果显示
            for enemy_down in enemies_down:
                enemies_down.remove(enemy_down)
                score += 1
                screen.blit(enemy_down.down_imgs, enemy_down.rect)  # 将爆炸的敌机画出来

            # 显示子弹
            player.bullets.draw(screen)
            # 显示敌机
            enemies1.draw(screen)
        else:
            screen_rect = screen.get_rect()
            largeText = pygame.font.Font('platech.ttf', 80)
            TextSurf, TextRect = text_objects('恭喜过关！', largeText)  # 通关标识
            TextRect.center = ((SCREEN_WIDTH/2), (SCREEN_HEIGHT/3))
            screen.blit(TextSurf, TextRect)

            # 设置按钮的尺寸和其他属性
            width, height = 200, 50
            button_color = (0, 255, 0)
            text_color = (255, 255, 255)
            font = pygame.font.SysFont(None, 48)

            # 创建按钮的rect对象，居中
            rect = pygame.Rect(0, 0, width, height)
            rect.center = screen_rect.center
            msg_image = font.render("Play", True, text_color,
                                    button_color)
            msg_image_rect = msg_image.get_rect()
            msg_image_rect.center = rect.center
            screen.fill(button_color, rect)
            screen.blit(msg_image, msg_image_rect)
            pressed = pygame.mouse.get_pressed()
            x1, y1 = pygame.mouse.get_pos()
            if x1 > 142 and y1 > 377:
                if x1 < 338 and y1 < 423:
                    if pressed[0]:
                        score = 0
        # 绘制得分
        score_font = pygame.font.Font(None, 36)
        if score > max_score:
            max_score = score
            with open('data.txt', 'w') as f:
                f.write(str(max_score))
        score_text = score_font.render(
            'score: {}/25 max score: {}'.format(str(score), max_score), True, (128, 128, 128))
        text_rect = score_text.get_rect()
        text_rect.topleft = [10, 10]
        screen.blit(score_text, text_rect)

    # 更新屏幕
    pygame.display.update()

    # 处理游戏退出
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    if move == 'right':
        player.moveRight()
    elif move == 'left':
        player.moveLeft()
    elif move == 'up':
        player.moveUp()
    elif move == 'down':
        player.moveDown()

# 游戏 Game Over 后显示最终得分
font = pygame.font.Font(None, 64)
text = font.render('Final Score: ' + str(score), True, (255, 0, 0))
text_rect = text.get_rect()
text_rect.centerx = screen.get_rect().centerx
text_rect.centery = screen.get_rect().centery + 24
screen.blit(game_over, (0, 0))
screen.blit(text, text_rect)

# 显示得分并处理游戏退出
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    pygame.display.update()
