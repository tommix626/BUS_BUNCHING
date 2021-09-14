# map editor for complicate roads
# v1.0.1

import json
import math
import random


def distance(x, y):
    return abs(x[0] - y[0]) + abs(x[1] - y[1])


size = 'small'
actionpointPosList = [[100, 100], [200, 100], [500, 100], [500, 300], [600, 300], [700, 300], [700, 500], [300, 500],
                      [100, 500]]  # 只能水平或竖直 否则要更新距离计算的公式
actionpointLengths = []
actionpointSigmas = []
sig_per_len = 0.05  # sigma per unit length
for i in range(len(actionpointPosList)):
    l = distance(actionpointPosList[i], actionpointPosList[(i + 1) % (len(actionpointPosList))])
    actionpointLengths.append(l)
    actionpointSigmas.append(l * sig_per_len)
tsigma = 0
for i in actionpointSigmas:
    tsigma += i ** 2
tsigma = math.sqrt(tsigma)
actionpoint_type = [0, 1, 0, 0, 1, 0, 0, 1, 0]  # 0-红绿灯 1-车站
busStopDict_StopNum2ActionIndex = {0: 1, 1: 4, 2: 7}  # 字典key做车站号，val做route中的下标
busStopBusesDict_ActionIndex2BusList = {1: [], 4: [], 7: []}  # 存到站车辆顺序
busStopTimeDict_ActionIndex2LastBusArrivalTime = {1: 0, 4: 0, 7: 0}  # 存到站车辆时间
tfcDurationDict_ActionIndex2DurLength = {0: 300, 2: 300, 3: 1000, 5: 300, 6: 300, 8: 300}  # 红灯绿灯时间 (in # of frame)
tfcStatus_dict_ActionIndex2Status = {0: random.randint(100, 1000), 2: 1, 3: random.randint(-1000, 100),
                                     5: random.randint(100, 1000),
                                     6: random.randint(100, 1000), 8: random.randint(100, 1000)}


save_Dict = {
    "actionpointPosList": actionpointPosList,
    "actionpointLengths": actionpointLengths,
    "actionpointSigmas": actionpointSigmas,
    "tsigma": tsigma,
    "actionpoint_type": actionpoint_type,
    "busStopDict_StopNum2ActionIndex": busStopDict_StopNum2ActionIndex,
    "busStopBusesDict_ActionIndex2BusList": busStopBusesDict_ActionIndex2BusList,
    "busStopTimeDict_ActionIndex2LastBusArrivalTime": busStopTimeDict_ActionIndex2LastBusArrivalTime,
    "tfcDurationDict_ActionIndex2DurLength": tfcDurationDict_ActionIndex2DurLength,
    "tfcStatus_dict_ActionIndex2Status": tfcStatus_dict_ActionIndex2Status,
}
with open(f"./config/{size}_map.json", "w") as f:
    json.dump(save_Dict, f, sort_keys=False, indent=4, separators=(',', ': '))
    print("加载入文件完成...")

with open(f"./config/{size}_map.json", 'r') as load_f:
    load_dict = json.load(load_f)
    print(load_dict)
