import matplotlib.pyplot as plt

# num waiting onbus
pNum, waitingList, onbusList = [], [], []

x = eval(input("stg="))
with open(f'strategy{x}', 'r') as f:
    lines = f.readlines()
    for line_num in range(len(lines)):
        if line_num % 3 == 0:
            pNum.append((float(lines[line_num].strip('\n'))))
        elif line_num % 3 == 1:
            waitingList.append((float(lines[line_num].strip('\n'))))
        elif line_num % 3 == 2:
            onbusList.append((float(lines[line_num].strip('\n'))))

# print(pNum, waitingList, onbusList,sep='\n')
plt.plot(pNum, waitingList, label="average waiting time")
plt.plot(pNum, onbusList, label="average on bus time")
plt.legend(bbox_to_anchor=(0.01, .92, .5, .1202), loc=3, \
           ncol=3, mode="None", borderaxespad=0.)
plt.title(f'strategy{x}')  # 图形标题
plt.xlabel("# of passenger delivered")  # x轴名称
plt.ylabel("frames")  # y 轴名称
plt.grid()
# plt.axis([0, 6, 0, 20])
plt.show()
