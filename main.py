# Bus bunching simulation
# v1.0.0
import pygame, sys
import random

# TODO make stops and turns into class and use .next to get the next target instead of fixed the road at first.

route = [[100, 100], [200, 100], [500, 100], [500, 300], [600, 300], [700, 300], [700, 500], [300, 500],
         [100, 500]]  # 只能水平或竖直 否则要更新距离计算的公式
route_type = [0, 1, 0, 0, 1, 0, 0, 1, 0]  # 0-红绿灯 1-车站
stop_dict = {0: 1, 1: 4, 2: 7}  # 字典key做车站号，val做route中的下标
stop_control_dict = {1: [], 4: [], 7: []}  # 存到站车辆顺序
tfc_time_dict = {0: 1000, 2: 1000, 3: 1000, 5: 1000, 6: 1000, 8: 1000}  # 红灯绿灯时间 (in # of frame)
tfc_dict = {0: random.randint(100, 1000), 2: 1, 3: random.randint(-1000, 100), 5: random.randint(100, 1000),
            6: random.randint(100, 1000), 8: random.randint(100, 1000)}
total_turn = len(route)  # 总事件数
total_stop = len(stop_dict)  # 总站数
car_color, road_color = [250, 100, 100], [50, 150, 50]  # 不再使用，颜色根据拥堵情况而改变
car_width, road_width = 8, 10
car_len = 10
bus_capacity = 40
# statistic
statDict = {'sucNum': 0,
            'total_waiting_time': 0,
            'total_onbus_time': 0}
stg=1

# TODO：拥堵 红绿灯 乘客（泊松）
# action：增加延迟 或者提升通行平均速度（公交专用道）
# 延迟还是提前 两个policy function
# 图神经网络
# TODO：左右对比界面 可以选择strategy n
# TODO：baseline 策略
def save_data(f):  # 数据保存 TODO：了解数据读取储存知识 并编写matplotlib程序读取不同strategy对应文件的信息绘制折线图
    sucNum = statDict['sucNum']
    total_waiting_time = statDict['total_waiting_time']
    total_onbus_time = statDict['total_onbus_time']
    if sucNum == 0:
        return
    avg_waiting_time, avg_onbus_time = total_waiting_time / sucNum, total_onbus_time / sucNum
    f.write(str(statDict['sucNum']))
    f.write('\n')
    f.write(str(avg_waiting_time))
    f.write('\n')
    f.write(str(avg_onbus_time))
    f.write('\n')
    print("check")


def sign(n):
    if (n > 0):
        return 1
    elif (n == 0):
        return 0
    else:
        return -1


def draw_grid(surface):  # todo: 加入拥堵路段彩色绘图
    # draw road
    for i in range(total_turn):
        s, s_next = i, (i + 1) % total_turn
        pygame.draw.line(surface, road_color, route[s], route[s_next], road_width)

    for i in range(total_turn):
        # draw bus stop
        if route_type[i] == 1:
            c = max(0, min(len(waitList[i]) * 10, 255))
            pygame.draw.circle(surface, (c, 0, 0), route[i], road_width, 0)
        # draw traffic light
        elif route_type[i] == 0:
            if (tfc_dict[i] > 0):  # green
                c = max(0, min(tfc_dict[i] // 2, 255))
                pygame.draw.circle(surface, (0, c, 0), route[i], road_width // 2, 0)
            else:  # red
                c = max(0, min(-tfc_dict[i] // 2, 255))
                pygame.draw.circle(surface, (c, 0, 0), route[i], road_width // 2, 0)


def add_passenger(wList, num=1):
    for i in range(num):
        t = stop_dict[random.randint(0, total_stop - 1)]
        wList[t].append(CLS_psg(t, time_global))
        return


def stat_display():
    sucNum = statDict['sucNum']
    total_waiting_time = statDict['total_waiting_time']
    total_onbus_time = statDict['total_onbus_time']
    if sucNum == 0:
        return
    avg_waiting_time, avg_onbus_time = total_waiting_time / sucNum, total_onbus_time / sucNum
    img_text_awt = fontScore.render(f"avg_waiting_time:{avg_waiting_time}", True, (0, 0, 255))
    img_text_aot = fontScore.render(f"avg_onbus_time:{avg_onbus_time}", True, (0, 0, 255))
    screen.blit(img_text_awt, (10, 10))
    screen.blit(img_text_aot, (10, 30))
    return


def tfc_update():
    for key in tfc_dict:
        if tfc_dict[key] > 1:
            tfc_dict[key] -= 1
            continue
        elif tfc_dict[key] < -1:
            tfc_dict[key] += 1
            continue
        if tfc_dict[key] == 1:
            tfc_dict[key] = -tfc_time_dict[key]
        elif tfc_dict[key] == -1:
            tfc_dict[key] = tfc_time_dict[key]


class CLS_Bus(object):
    def __init__(self, num, surf, wList):
        self.stopNum = num % total_turn  # 将要到达的站在route里的下标
        self.pos = route[self.stopNum]
        self.target = route[(num + 1) % total_turn]
        self.num = num
        self.direction = [0, 0]
        self.surface = surf
        self.psgNum = 0
        self.pList = []
        self.status = 1  # 1是行车 0是上下客 -1是等红绿灯
        self.cd_down, self.cd_pick = 0, 0
        self.waitList = wList
        self.sucList = []

    def move(self):
        # move
        self.draw()
        dx, dy = sign(self.target[0] - self.pos[0]) * max(0.1, random.random()), \
                 sign(self.target[1] - self.pos[1]) * max(0.1,
                                                          random.random())  # FIXME: strategy0 random-small turbulance
        if self.status == 0:
            dx, dy = 0, 0
            stop_num = (self.stopNum - 1) % total_turn
            if stop_control_dict[stop_num][0] != self:  # 如果不是排在第一辆的车
                if random.random() <= 1:  # 不上客 FIXME 把上客变成整个过程一起算 难点在于上到一半来新车要更新分布
                    return
            tag = self.lower_psg() * self.pick_psg()
            # print(tag, random.random())
            if tag == 0:  # either is not done, the bus won't start
                return
            self.status = 1
            stop_control_dict[stop_num].remove(self)
        elif self.status == -1:
            dx, dy = 0, 0
            if tfc_dict[(self.stopNum - 1) % total_turn] > 0:
                self.status = 1
        x, y = self.pos[0] + dx, self.pos[1] + dy
        self.pos = [x, y]
        # when arrive at target
        if -0.5 < self.pos[0] - self.target[0] < 0.5 and -0.5 < self.pos[1] - self.target[1] < 0.5:
            self.pos = self.target
            # check event
            if route_type[self.stopNum] == 1:  # if bus stop
                self.status = 0
                stop_control_dict[self.stopNum].append(self)
            elif route_type[self.stopNum] == 0:  # if cross road
                self.status = -1
            # update target
            self.stopNum = (self.stopNum + 1) % total_turn
            self.target = route[self.stopNum]
        return

    def draw(self):  # 交给主循环来做还是这里做 到底哪个好？
        if self.direction[0] != 0:
            w, h = car_len, car_width
        else:
            w, h = car_width, car_len
        x, y = self.pos[0] - w // 2, self.pos[1] - h // 2
        c = 200 - len(self.pList) * (200 // bus_capacity)
        pygame.draw.rect(self.surface, (250, c, c), (int(x), int(y), w, h), 0)
        return

    def lower_psg(self):
        if self.cd_down > 0:
            self.cd_down -= 1
            return 0
        for i in self.pList:
            if i.dest == (self.stopNum - 1) % total_turn:
                self.cd_down += 50  # take 50 frame to go down
                i.wait_time[1] += time_global
                self.sucList.append(i)
                statDict['sucNum'] += 1
                statDict['total_waiting_time'] += i.wait_time[0]
                statDict['total_onbus_time'] += i.wait_time[1]
                save_data(f)
                self.pList.remove(i)
                return 0
        return 1

    def pick_psg(self):
        if self.cd_pick > 0:
            self.cd_pick -= 1
            return 0
        if len(self.pList) >= bus_capacity:
            return 1
        for i in self.waitList[(self.stopNum - 1) % total_turn]:
            if i.start == (self.stopNum - 1) % total_turn:
                self.cd_pick += 70  # take 70 frame to pick up(因为要刷卡所以慢一些)
                self.pList.append(i)
                i.wait_time[0] += time_global
                i.wait_time[1] -= time_global
                self.waitList[(self.stopNum - 1) % total_turn].remove(i)
                return 0
        return 1


class CLS_psg(object):
    def __init__(self, start, time):
        self.start = start
        self.dest = stop_dict[(list(stop_dict.keys())[list(stop_dict.values()).index(self.start)] + \
                               random.randint(1, total_stop - 1)) % total_stop]  # 不能上完就下 FIXME 确认是否为站台 bosong分布确定下客目的地
        self.wait_time = [-time, 0]  # record the frame of the waiting and on-bus time
        self.status = 0  # 0-(waiting for bus) 1-(on bus) 2-(reach destination)
        # print(self.start, self.dest)


# pygame初始化
pygame.init()
screen = pygame.display.set_mode((800, 600))
fontScore = pygame.font.Font(None, 28)
clock = pygame.time.Clock()
f = open(f'strategy{stg}', 'w')
# 用户程序初始化
busList = []  # todo: 再维护一个以num为键值的字典 方便计算前后距离
waitList = [[] for i in range(total_turn)]  # waitList = [[]] * total_turn 这样的话wList的子元素空list是共用一个地址的 不可取！
time_global = 0
for i in range(total_turn):
    if route_type[i] == 1:
        busList.append(CLS_Bus(i, screen, waitList))
# 主循环
while True:
    time_global += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            f.close()
        # 其他鼠标键盘事件
    screen.fill((100, 100, 100))
    # 主程序
    draw_grid(screen)
    if random.random() < 0.01:  # TODO:bossoin dist quantify
        add_passenger(waitList)
    tfc_update()
    for bus in busList:
        bus.move()
    stat_display()
    pygame.display.update()

    #clock.tick(500)
