'''
添加音效
    1.创建我方坦克
    2.我方坦克发射子弹
'''
import pygame,time,random
from pygame.sprite import Sprite
#定义常量
SCREEN_WIDTH = 750
SCREEN_HEIGHT= 500
BG_COLOR = pygame.Color(0,0,0)
TEXT_COLOR = pygame.Color(255,0,0)
#创建精灵基类
class BaseItem(Sprite):
    pass

class MainGame():
    window = None
    myTank = None
    enemyCount = 5
    enemyList = []
    #定义我方坦克发射的子弹列表
    myBulletList = []
    #定义敌方坦克发射的子弹列表
    enemyBulletList = []
    #定义存储爆炸效果类列表
    explodeList =[]
    #定义墙壁列表
    wallList = []
    #初始化方法
    def __init__(self) -> None:
        pass
    #创建敌方坦克
    def createEnemyTank(self):
        top = 100
        for i in range(MainGame.enemyCount):
            left = random.randint(0,600)
            speed = random.randint(1,4)
            enemyTank = EnemyTank(left,top,speed)
            #添加到列表
            MainGame.enemyList.append(enemyTank)

    #加载敌方坦克
    def displayEnemyTank(self):
        for enemyTank in MainGame.enemyList:
            #判断敌方坦克是否存活
            if enemyTank.live:
                enemyTank.displayTank()
                #调用move进行移动
                enemyTank.randMove()
                #初始化敌方坦克发射的子弹
                #调用检测敌方坦克是否与墙壁发生碰撞
                enemyTank.tank_hit_wall()
                #调用检测敌方坦克是否与我方坦克发生碰撞
                if MainGame.myTank and MainGame.myTank.live:
                    enemyTank.enemyTank_hit_myTank()
                enemyBullet = enemyTank.shot()
                #判断子弹是否有值
                if enemyBullet:
                    MainGame.enemyBulletList.append(enemyBullet)
            else:#当前敌方坦克已经死亡，从敌方坦克列表移除
                MainGame.enemyList.remove(enemyTank)


    #显示我方坦克发射的子弹
    def displayMyBullet(self):
        for myBullet in MainGame.myBulletList:
            #判断子弹是否存活
            if myBullet.live :
                myBullet.displayBullet()
                #调用子弹的移动方法
                myBullet.move()
                #调用我方子弹是否与敌方坦克碰撞
                myBullet.myBullet_hit_enemyTank()
                #调用检测我方子弹是否与墙壁发生碰撞
                myBullet.bullet_hit_wall()
            else:
                #从子弹列表中删除子弹
                MainGame.myBulletList.remove(myBullet)

    #显示敌方坦克发射的子弹
    def displayEnemyBullet(self):
        for enemyBullet in MainGame.enemyBulletList:
            #判断子弹是否存活
            if enemyBullet.live:
                enemyBullet.displayBullet()
                #调用子弹移动的方法
                enemyBullet.move()
                #调用敌方子弹与我方坦克碰撞检测
                enemyBullet.enemyBullet_hit_myTank()
                #调用检测敌方子弹是否与墙壁发生碰撞
                enemyBullet.bullet_hit_wall()
            else:
                #从子弹列表删除
                MainGame.enemyBulletList.remove(enemyBullet)

    #循环遍历爆炸效果列表展示爆炸效果
    def displayExplodeList(self):
        for explode in MainGame.explodeList:
            #判断是否存活
            if explode.live:
                #展示
                explode.displayExplode()
            else:
                #从爆炸效果列表中移除
                MainGame.explodeList.remove(explode)

    #创建我方坦克
    def createMyTank(self):
        MainGame.myTank = MyTank(350,300)
        #添加音效
        music = Music('./img/start.wav')
        #播放
        music.playMusic()

    #创建墙壁
    def createWall(self):
        top = 220
        for i in range(6):
            #初始化墙壁
            wall = Wall(i*130,top)
            #添加到墙壁列表
            MainGame.wallList.append(wall)

    #加载墙壁
    def displayWallList(self):
        #循环遍历墙壁列表
        for wall in MainGame.wallList:
            if wall.live:
                wall.displayWall()
            else:
                #从墙壁列表中移除
                MainGame.wallList.remove(wall)
    #开始游戏
    def startGame(self):
      #初始化窗口
      pygame.display.init()
      #设置窗口大小
      MainGame.window = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
      #设置窗口的标题
      pygame.display.set_caption('坦克大战1.05')

      #初始化我方坦克
      self.createMyTank()

      #调用创建敌方坦克
      self.createEnemyTank()

      #创建墙壁
      self.createWall()
      while True:
        time.sleep(0.02)
        #给窗口设置填充色
        MainGame.window.fill(BG_COLOR)
        #添加文字信息提示
        textSurface = self.getTextSurface('敌方坦克剩余数量%d'%len(MainGame.enemyList))
        #主窗口显示文字信息
        MainGame.window.blit(textSurface,(10,10))
        #添加事件监听
        self.getEvent()

        #调用坦克的显示方法
        if MainGame.myTank and MainGame.myTank.live:
            MainGame.myTank.displayTank()
        else:
            #删除我方坦克
            del MainGame.myTank
            MainGame.myTank = None

        #调用坦克移动的方法
        if MainGame.myTank and MainGame.myTank.live :
            if not MainGame.myTank.stop:
                MainGame.myTank.move()
                #调用检测我方坦克是否与墙壁发生碰撞
                MainGame.myTank.tank_hit_wall()
                #调用检测我方坦克是否与敌方坦克发生碰撞
                MainGame.myTank.myTank_hit_enemyTank()


        #加载敌方坦克
        self.displayEnemyTank()

        #加载我方坦克发射的子弹
        self.displayMyBullet()

        #加载敌方坦克发射的子弹
        self.displayEnemyBullet()

        #加载爆炸效果
        self.displayExplodeList()

        #加载墙壁
        self.displayWallList()
        pygame.display.update()


    #结束游戏
    def endGame(self):
        print('谢谢使用，欢迎再次使用')
        exit()

    #添加文字信息提示
    def getTextSurface(self,text):
        #初始化字体模块
        pygame.font.init()
        #获取所有字体
        # print(pygame.font.get_fonts())
        #获取字体对象
        font = pygame.font.SysFont('kaiti',18)
        #绘制文字信息
        textSurface = font.render(text,True,TEXT_COLOR)
        return textSurface

    #添加事件监听
    def getEvent(self):
        #获取所有的事件
        eventList = pygame.event.get()
        #遍历事件
        for event in eventList:
            #判断按下是否是关闭
            if event.type == pygame.QUIT:
                self.endGame()

            #判断是否是键盘事件
            if event.type == pygame.KEYDOWN:
                #判断我方坦克是否消亡
                if not MainGame.myTank:
                    #判断键盘按下的是Esc键
                    if event.key == pygame.K_ESCAPE:
                        #调用创建我方坦克的方法
                        self.createMyTank()
                if MainGame.myTank and MainGame.myTank.live:
                    #判断按下的是上 下 左 右
                    if event.key == pygame.K_LEFT:
                        print('按下左键,坦克向左移动')
                        #修改我方坦克的方向
                        MainGame.myTank.direction='L'
                        #修改坦克移动开关
                        MainGame.myTank.stop=False

                    elif event.key == pygame.K_RIGHT:
                        print('按下右键，坦克向右移动')
                        #修改我方坦克的方向
                        MainGame.myTank.direction='R'
                        #修改坦克移动开关
                        MainGame.myTank.stop=False

                    elif event.key == pygame.K_UP:
                        print('按下上键，坦克向上移动')
                        #修改我方坦克的方向
                        MainGame.myTank.direction='U'
                        #修改坦克移动开关
                        MainGame.myTank.stop=False

                    elif event.key == pygame.K_DOWN:
                        print('按下下键，坦克向下移动')
                        #修改我方坦克的方向
                        MainGame.myTank.direction='D'
                        #修改坦克移动开关
                        MainGame.myTank.stop=False

                    elif event.key == pygame.K_SPACE:
                        print('发射子弹')
                        #子弹列表的数量如果小于3，可以初始化子弹
                        if len(MainGame.myBulletList)<3:
                            #初始化子弹
                            myBullet = Bullet(MainGame.myTank)
                            MainGame.myBulletList.append(myBullet)
                            #添加音效
                            music = Music('./img/fire.wav')
                            music.playMusic()



            #判断键盘键是否松开
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_UP or event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                    if MainGame.myTank and MainGame.myTank.live:
                        MainGame.myTank.stop = True






class Tank(BaseItem):
    def __init__(self,left,top) -> None:
        #保存加载的图片
        self.images = {
            'U':pygame.image.load('./img/p1tankU.gif'),
            'D':pygame.image.load('./img/p1tankD.gif'),
            'L':pygame.image.load('./img/p1tankL.gif'),
            'R':pygame.image.load('./img/p1tankR.gif'),
        }
        #设置坦克的方向
        self.direction = 'D'
        #根据坦克方向，获取加载的图片
        self.image = self.images.get(self.direction)
        #根据图片获取图片的矩形区域
        self.rect = self.image.get_rect()
        #设置区域的left和top
        self.rect.left = left
        self.rect.top = top

        #速度
        self.speed = 5

        #坦克移动开关
        self.stop = True

        #生存状态
        self.live = True

        #移动之前的位置
        self.oldleft = self.rect.left
        self.oldtop = self.rect.top

    #展示坦克的方法
    def displayTank(self):
        self.image = self.images.get(self.direction)
        #调用blit方法展示坦克
        MainGame.window.blit(self.image,self.rect)

    #移动坦克
    def move(self):
        #记录移动之前的位置
        self.oldleft = self.rect.left
        self.oldtop = self.rect.top
        #判断坦克的方向
        if self.direction == 'L':
            if self.rect.left>0:
                self.rect.left -= self.speed
        elif self.direction == 'R':
            if self.rect.left+self.rect.height<SCREEN_WIDTH:
                self.rect.left += self.speed
        elif self.direction == 'U':
            if self.rect.top >0:
                self.rect.top -= self.speed
        elif self.direction == 'D':
            if self.rect.top+self.rect.height<SCREEN_HEIGHT:
                self.rect.top += self.speed

    #射击
    def shot(self):
      pass

    #设置坦克位置为移动之前的位置
    def stay(self):
        self.rect.left = self.oldleft
        self.rect.top = self.oldtop

    #检测坦克是否与墙壁发生碰撞
    def tank_hit_wall(self):
        #循环遍历墙壁列表
        for wall in MainGame.wallList:
            if pygame.sprite.collide_rect(self,wall):
                #设置坦克的坐标为移动之前的位置
                self.stay()

#我方坦克
class MyTank(Tank):
    #初始化方法
    def __init__(self,left,top) -> None:
        #调用父类的初始方法
        super(MyTank,self).__init__(left,top)

    #检测我方坦克是否与敌方坦克发生碰撞
    def myTank_hit_enemyTank(self):
        #循环遍历敌方坦克列表
        for enemyTank in MainGame.enemyList:
            if pygame.sprite.collide_rect(self,enemyTank):
                self.stay()

#敌方坦克
class EnemyTank(Tank):
    def __init__(self,left,top,speed) -> None:
        #调用父类的初始化方法
        super(EnemyTank,self).__init__(left,top)
        #加载保存的图片集
        self.images= {
            'U':pygame.image.load('./img/enemy1U.gif'),
            'D':pygame.image.load('./img/enemy1D.gif'),
            'L':pygame.image.load('./img/enemy1L.gif'),
            'R':pygame.image.load('./img/enemy1R.gif'),
        }
        #设置敌方坦克方向
        self.direction = self.randDirection()
        #根据方向获取图片
        self.image = self.images.get(self.direction)
        #获取矩形区域
        self.rect = self.image.get_rect()
        #设置left  top
        self.rect.left = left
        self.rect.top = top
        self.speed = speed

        #步数
        self.step = 60

    #随机生成方向
    def randDirection(self):
        num = random.randint(1,4)
        if num == 1:
            return 'U'
        elif num == 2:
            return 'D'
        elif num == 3:
            return 'L'
        elif num == 4:
            return 'R'

    #随机移动的方法
    def randMove(self):
        if self.step <=0:
            #修改敌方坦克的方向
            self.direction = self.randDirection()
            #让步数复位
            self.step = 60
        else:
            self.move()
            #步数递减
            self.step-=1

    def shot(self):
        #随机生成100以内的数
        num = random.randint(0,100)
        if num<10:
            return Bullet(self)

    #检测敌方坦克是否与我方坦克发生碰撞
    def enemyTank_hit_myTank(self):
        if pygame.sprite.collide_rect(self,MainGame.myTank):
            self.stay()



#子弹类
class Bullet(BaseItem):
    def __init__(self,tank) -> None:
        #加载图片
        self.image = pygame.image.load('./img/enemymissile.gif')
        #子弹的方向
        self.direction = tank.direction
        #根据图片获取区域
        self.rect = self.image.get_rect()
        #设置left top
        if self.direction == 'U':
            self.rect.left = tank.rect.left + tank.rect.width/2 - self.rect.width/2
            self.rect.top = tank.rect.top - self.rect.height
        elif self.direction == 'D':
            self.rect.left = tank.rect.left + tank.rect.width / 2 - self.rect.width / 2
            self.rect.top = tank.rect.top + tank.rect.height
        elif self.direction == 'L':
            self.rect.left = tank.rect.left - self.rect.width / 2 - self.rect.width / 2
            self.rect.top = tank.rect.top + tank.rect.width / 2 - self.rect.width / 2
        elif self.direction == 'R':
            self.rect.left = tank.rect.left + tank.rect.width
            self.rect.top = tank.rect.top + tank.rect.width / 2 - self.rect.width / 2
        #子弹的速度
        self.speed = 6

        #是否存活
        self.live = True

    #展示子弹
    def displayBullet(self):
        #将图片加载到窗口
        MainGame.window.blit(self.image,self.rect)

    #移动
    def move(self):
        if self.direction == 'U':
            if self.rect.top>0:
                self.rect.top -= self.speed
            else: #碰到墙壁
                self.live = False
        elif self.direction == 'D':
            if self.rect.top + self.rect.height < SCREEN_HEIGHT:
                self.rect.top += self.speed
            else:
                self.live = False
        elif self.direction == 'L':
            if self.rect.left>0:
                self.rect.left -= self.speed
            else:
                self.live = False
        elif self.direction == 'R':
            if self.rect.left + self.rect.width < SCREEN_WIDTH:
                self.rect.left += self.speed
            else:
                self.live = False

    #我方子弹与敌方坦克碰撞检测
    def myBullet_hit_enemyTank(self):
        #循环遍历敌方坦克列表
        for enemyTank in MainGame.enemyList:
            if pygame.sprite.collide_rect(self,enemyTank):
                #修改敌方坦克与我方子弹的生存状态
                enemyTank.live = False
                self.live = False
                #初始化爆炸效果类
                explode = Explode(enemyTank)
                #添加爆炸效果类到爆炸效果列表中
                MainGame.explodeList.append(explode)

    #敌方子弹与我方坦克发生碰撞
    def enemyBullet_hit_myTank(self):
        if MainGame.myTank and MainGame.myTank.live:
            if pygame.sprite.collide_rect(self,MainGame.myTank):
                #产生爆炸效果
                explode = Explode(MainGame.myTank)
                #将爆炸效果添加到爆炸效果列表
                MainGame.explodeList.append(explode)
                #修改敌方子弹与我方坦克的生存状态
                self.live = False
                MainGame.myTank.live = False

    #检测子弹是否与墙壁发生碰撞
    def bullet_hit_wall(self):
        #循环遍历墙壁列表
        for wall in MainGame.wallList:
            if pygame.sprite.collide_rect(self,wall):
                #设置子弹生存状态修改
                self.live = False
                #让墙壁的生命值减减
                wall.hp -=1
                #判断墙壁生命值是否小于等于0
                if wall.hp<=0:
                    #设置墙壁的生存状态
                    wall.live = False


#墙壁类
class Wall():
    def __init__(self,left,top) -> None:
        #加载墙壁图片
        self.image = pygame.image.load('./img/steels.gif')
        #根据图片获取区域
        self.rect = self.image.get_rect()
        #设置left top
        self.rect.left = left
        self.rect.top = top
        #生存状态
        self.live = True
        #生命值
        self.hp = 3

    #展示墙壁方法
    def displayWall(self):
        MainGame.window.blit(self.image,self.rect)
#爆炸效果类
class Explode():
    def __init__(self,tank) -> None:
        #爆炸的位置是当前子弹击中坦克的位置
        self.rect = tank.rect
        self.images = [
            pygame.image.load('./img/blast0.gif'),
            pygame.image.load('./img/blast1.gif'),
            pygame.image.load('./img/blast2.gif'),
            pygame.image.load('./img/blast3.gif'),
            pygame.image.load('./img/blast4.gif'),
        ]
        self.step = 0
        self.image = self.images[self.step]
        #生存状态
        self.live = True


    #展示爆炸效果
    def displayExplode(self):
        if self.step<len(self.images):
            self.image = self.images[self.step]
            self.step+=1
            #添加到主窗口
            MainGame.window.blit(self.image,self.rect)
        else:
            #修改存活状态
            self.live = False
            self.step = 0


#音效类
class Music():

    def __init__(self,filename) -> None:
        self.filename = filename
        #初始化混合器
        pygame.mixer.init()
        #加载音乐
        pygame.mixer.music.load(self.filename)

    #播放音乐
    def playMusic(self):
        pygame.mixer.music.play()

#主方法
if __name__ == '__main__':
  #调用主类中startGame()
  MainGame().startGame()
  # MainGame().getTextSurface('aa')
