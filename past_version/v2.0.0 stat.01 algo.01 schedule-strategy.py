# Bus bunching simulation
# v2.0.0 stat.01 algo.01 schedule-strategy
import math
from typing import Dict

import numpy as np
import pygame, sys
import random

# TODO (important) make stops and turns into class and use .next to get the next target instead of fixed the road at first.
c_bar = 2
sigma = 2000
stopNum = 20
stopTime = []
# hList=[]


actionpointPosList = [[100, 100], [200, 100], [500, 100], [500, 300], [600, 300], [700, 300], [700, 500], [300, 500],
                      [100, 500]]  # 只能水平或竖直 否则要更新距离计算的公式
actionpointLengths = [100, 300, 200, 100, 100, 200, 400, 200, 400]
actionpointSigmas = [5, 15, 10, 5, 5, 10, 20, 10, 20]
actionpoint_type = [0, 1, 0, 0, 1, 0, 0, 1, 0]  # 0-红绿灯 1-车站
busStopDict_StopNum2ActionIndex = {0: 1, 1: 4, 2: 7}  # 字典key做车站号，val做route中的下标
busStopBusesDict_ActionIndex2BusList = {1: [], 4: [], 7: []}  # 存到站车辆顺序
busStopTimeDict_ActionIndex2LastBusArrivalTime = {1: 0, 4: 0, 7: 0}  # 存到站车辆时间
tfcDurationDict_ActionIndex2DurLength = {0: 300, 2: 300, 3: 1000, 5: 300, 6: 300, 8: 300}  # 红灯绿灯时间 (in # of frame)
tfcStatus_dict_ActionIndex2Status = {0: random.randint(100, 1000), 2: 1, 3: random.randint(-1000, 100),
                                     5: random.randint(100, 1000),
                                     6: random.randint(100, 1000), 8: random.randint(100, 1000)}
total_actionsNum = len(actionpointPosList)  # 总事件数（站+红绿灯）
total_stopsNum = len(busStopDict_StopNum2ActionIndex)  # 总站数
car_color, road_color = [250, 100, 100], [50, 150, 50]  # 不再使用，颜色根据拥堵情况而改变
car_width, road_width = 8, 10
car_len = 10
bus_capacity = 40
# statistic
statDict = {'sucNum': 0,
            'total_waiting_time': 0,
            'total_onbus_time': 0,
            'avg_waiting_time': 0,
            'avg_onbus_time': 0}
stg = "schedule"

# TODOs
# TODO：拥堵 红绿灯 乘客（泊松）
# TODO: action：增加延迟 或者提升通行平均速度（公交专用道）
# TODO: 延迟还是提前 两个policy function
# TODO: 图神经网络
# TODO：单独界面+自动排版 可以选择strategy n
# TODO：baseline 策略

def save_data(f):  # 数据保存 TODO：了解数据读取储存知识 并编写matplotlib程序读取不同strategy对应文件的信息绘制折线图（more:实时更新）
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
    if n > 0:
        return 1
    elif n == 0:
        return 0
    else:
        return -1


def Calculate_distance(p1, p2):
    r_sq2 = (p1[0] - p2[0]) ** 2 + (p2[1] - p1[1]) ** 2
    return int(math.sqrt(r_sq2))


# 绘制路线图
def draw_grid(surface):  # todo: 加入拥堵路段彩色绘图
    # draw road
    for i in range(total_actionsNum):
        s, s_next = i, (i + 1) % total_actionsNum
        pygame.draw.line(surface, road_color, actionpointPosList[s], actionpointPosList[s_next], road_width)

    for i in range(total_actionsNum):
        # draw bus stop
        if actionpoint_type[i] == 1:
            c = max(0, min(len(waitList[i]) * 10, 255))
            pygame.draw.circle(surface, (c, 0, 0), actionpointPosList[i], road_width, 0)
        # draw traffic light
        elif actionpoint_type[i] == 0:
            if (tfcStatus_dict_ActionIndex2Status[i] > 0):  # green
                c = max(0, min(tfcStatus_dict_ActionIndex2Status[i] // 2, 255))
                pygame.draw.circle(surface, (0, c, 0), actionpointPosList[i], road_width // 2, 0)
            else:  # red
                c = max(0, min(-tfcStatus_dict_ActionIndex2Status[i] // 2, 255))
                pygame.draw.circle(surface, (c, 0, 0), actionpointPosList[i], road_width // 2, 0)


# 向站点添加乘客
def add_passenger(wList, num=1):
    for i in range(num):
        t = busStopDict_StopNum2ActionIndex[random.randint(0, total_stopsNum - 1)]
        wList[t].append(CLS_psg(t, time_global))
        return


# 计算数据
def stat_calculation(i):
    i.wait_time[1] += time_global
    statDict['sucNum'] += 1
    statDict['total_waiting_time'] += i.wait_time[0]
    statDict['total_onbus_time'] += i.wait_time[1]
    statDict['avg_waiting_time'] = statDict['total_waiting_time'] // statDict['sucNum']
    statDict['avg_onbus_time'] = statDict['total_onbus_time'] // statDict['sucNum']


# 展示数据
def stat_display():
    fontScore = pygame.font.Font(None, 28)
    pos = [10, 10]
    # prevent divide by ZERO error
    if statDict['sucNum'] == 0:
        return

    for k, v in statDict.items():
        img_text = fontScore.render(f"{k}:{v}", True, (0, 0, 255))
        screen.blit(img_text, pos)
        pos[1] += 20
    return


# traffic light status update
def tfc_update():
    for key in tfcStatus_dict_ActionIndex2Status:
        if tfcStatus_dict_ActionIndex2Status[key] > 1:
            tfcStatus_dict_ActionIndex2Status[key] -= 1
            continue
        elif tfcStatus_dict_ActionIndex2Status[key] < -1:
            tfcStatus_dict_ActionIndex2Status[key] += 1
            continue
        if tfcStatus_dict_ActionIndex2Status[key] == 1:
            tfcStatus_dict_ActionIndex2Status[key] = -tfcDurationDict_ActionIndex2DurLength[key]
        elif tfcStatus_dict_ActionIndex2Status[key] == -1:
            tfcStatus_dict_ActionIndex2Status[key] = tfcDurationDict_ActionIndex2DurLength[key]


class CLS_Bus(object):
    def __init__(self, initStopNum, surf, wList):
        self.actionpointIndex = initStopNum % total_actionsNum  # 将要到达的站在route里的下标
        self.pos = actionpointPosList[self.actionpointIndex]
        self.target = actionpointPosList[(initStopNum + 1) % total_actionsNum]
        self.lastTarget = actionpointPosList[initStopNum % total_actionsNum]
        self.num = initStopNum
        self.direction = [0, 0]
        self.surface = surf
        self.psgNum = 0
        self.pList = []
        self.status = 1  # 1是行车 0是上下客 -1是等红绿灯
        self.cd_down, self.cd_pick = 0, 0
        self.waitList = wList
        self.sucList = []
        self.speed = c_bar  # 加入速度 方便用strategy进行控制
        self.segIndex, self.segLength = initStopNum % total_actionsNum, 0  # 路段编号和路段上编号
        self.facing = 1  # 顺时针1 逆时针-1
        self.B2Bdistance = []  # TODO:add a framework that save all the value of
        self.schedule = 0

    def BusMainMove(self):
        # move
        # self.probe() #探测状态并加减速
        self.draw()
        dx, dy = sign(self.target[0] - self.pos[0]) * max(0.1, random.random()), \
                 sign(self.target[1] - self.pos[1]) * max(0.1, random.random())  # FIXME: strategy0
        # 上下客时
        if self.status == 0:
            dx, dy = 0, 0
            stop_num = (self.actionpointIndex - 1) % total_actionsNum
            if busStopBusesDict_ActionIndex2BusList[stop_num][0] != self:  # 如果不是排在第一辆的车
                if random.random() <= 1:  # 不上客 FIXME 把上客变成整个过程一起算 难点在于上到一半来新车要更新分布
                    return
            tag = self.lower_psg() * self.pick_psg()
            # print(tag, random.random())
            if tag == 0 or time_global < self.schedule:  # either is not done, the bus won't start or not start until scheduled
                return
            self.status = 1
            #self.get_new_speed()
            self.schedule_update()  # update schedule
            busStopBusesDict_ActionIndex2BusList[stop_num].remove(self)
        # 等红绿灯
        elif self.status == -1:
            dx, dy = 0, 0
            if tfcStatus_dict_ActionIndex2Status[(self.actionpointIndex - 1) % total_actionsNum] > 0:
                self.status = 1
                self.get_new_speed()
        x, y = self.pos[0] + dx * self.speed, self.pos[1] + dy * self.speed
        self.pos = [x, y]
        # when arrive at target
        if -0.5 < self.pos[0] - self.target[0] < 0.5 and -0.5 < self.pos[1] - self.target[1] < 0.5:
            self.pos = self.target
            # check event
            if actionpoint_type[self.actionpointIndex] == 1:  # if target==bus stop
                self.status = 0
                busStopBusesDict_ActionIndex2BusList[self.actionpointIndex].append(self)
            elif actionpoint_type[self.actionpointIndex] == 0:  # if target==cross road
                self.status = -1
            # update target
            self.lastTarget = self.target
            self.segIndex = self.actionpointIndex
            self.actionpointIndex = (self.actionpointIndex + 1) % total_actionsNum
            self.target = actionpointPosList[self.actionpointIndex]
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
            if i.dest == (self.actionpointIndex - 1) % total_actionsNum:
                self.cd_down += 50  # take 50 frame to go down
                self.sucList.append(i)
                stat_calculation(i)
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
        for i in self.waitList[(self.actionpointIndex - 1) % total_actionsNum]:
            if i.start == (self.actionpointIndex - 1) % total_actionsNum:
                self.cd_pick += 70  # take 70 frame to pick up(因为要刷卡所以慢一些)
                self.pList.append(i)
                i.wait_time[0] += time_global
                i.wait_time[1] -= time_global
                self.waitList[(self.actionpointIndex - 1) % total_actionsNum].remove(i)
                return 0
        return 1

    def probe(self):
        self.segLength = Calculate_distance(self.lastTarget, self.pos)

    def get_new_speed(self):
        # tg,tl=time_global,busStopTimeDict_ActionIndex2LastBusArrivalTime[self.actionpointIndex]
        l = Calculate_distance(self.lastTarget, self.target)
        t = np.random.normal(l / c_bar, sigma)
        print(l)
        self.speed = 2  # FIXME
        if (self.speed <= 0):
            print("EROR")
        # h=tg-tl

    def schedule_update(self):
        delay, sigma=0, 0
        action_idx=self.segIndex
        delay += actionpointLengths[action_idx]/c_bar
        sigma += actionpointSigmas[action_idx]
        action_idx = (action_idx + 1) % total_actionsNum
        while(1):
            if actionpoint_type[action_idx]==0:
                delay += tfcDurationDict_ActionIndex2DurLength[action_idx]//2  # IMP: delay half the time of red light
            elif actionpoint_type[action_idx]==1:
                break
            delay += actionpointLengths[action_idx] / c_bar
            sigma += actionpointSigmas[action_idx]
            action_idx = (action_idx + 1) % total_actionsNum
        self.schedule = time_global + np.random.normal(delay, sigma)


class CLS_psg(object):
    def __init__(self, start, time):
        self.start = start
        self.dest = busStopDict_StopNum2ActionIndex[(list(busStopDict_StopNum2ActionIndex.keys())[
                                                         list(busStopDict_StopNum2ActionIndex.values()).index(
                                                             self.start)] + \
                                                     random.randint(1,
                                                                    total_stopsNum - 1)) % total_stopsNum]  # 不能上完就下 FIXME 确认是否为站台 bosong分布确定下客目的地
        self.wait_time = [-time, 0]  # record the frame of the waiting and on-bus time
        self.status = 0  # 0-(waiting for bus) 1-(on bus) 2-(reach destination)
        # print(self.start, self.dest)


# pygame初始化
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
f = open(f'strategy{stg}', 'w')
# 用户程序初始化
busList = []  # todo: 再维护一个以num为键值的字典 方便计算前后距离
waitList = [[] for i in range(total_actionsNum)]  # waitList = [[]] * total_turn 这样的话wList的子元素空list是共用一个地址的 不可取！
time_global = 0
for i in range(total_actionsNum):
    if actionpoint_type[i] == 1:
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
        bus.BusMainMove()
    stat_display()
    pygame.display.update()

    #clock.tick(500)
