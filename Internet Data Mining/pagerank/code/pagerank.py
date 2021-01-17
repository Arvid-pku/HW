import json
import time
pr = {}
newpr = {}
inedge = {}
outedge = {}
outnum = {}
mylen = 0

# 产生出边，入边，出边数列表
def makewd(filepath):
    global outedge
    global inedge
    global outnum
    with open(filepath, 'r') as f:
       outedge = json.load(f)
    for wd in outedge.keys():
        inedge[wd] = []
    for item in outedge.items():
        outnum[item[0]] = len(item[1])
        for ined in item[1]:
            inedge[ined].append(item[0])

# 初始化
def initpr(pr):
    global mylen
    for node in outedge.keys():
        pr[node] = 1/mylen
    return pr

# 计算PageRank值
def calpagerank(p, epsilon, maxit):
    global pr
    global outedge
    global mylen
    mylen = len(outedge)
    pr = initpr(pr)
    it = 0
    loss = epsilon + 1e-10
    # 迭代
    while(loss > epsilon and it < maxit):
        loss = 0
        newpr = {}
        newpr = initpr(newpr)
        # 更新
        for item in inedge.items():
            if item[1]:
                tmp = (1-p)/mylen
                for inlink in item[1]:
                    tmp = tmp + pr[inlink]/outnum[inlink]                
                newpr[item[0]] = tmp
            loss = loss + abs(pr[item[0]]-newpr[item[0]])

        # 计算平均误差
        loss = loss / mylen
        print(loss)
        it = it + 1
        print(it)
        pr = newpr
    

if __name__ == "__main__":
    makewd('graph.json')
    # 时间
    start = time.time()
    calpagerank(0.85, 1e-7, 10)
    print(f'time: {time.time()-start}')
    # 储存结果
    # with open('sortrank2.json', 'w') as f:
        # json.dump(dict(sorted(pr.items(), key=lambda item: -item[1])), f, indent=4)
    f = open('pagerankResult.txt', 'w')
    for item in list(pr.items()):
        f.write(f'{item[0]}\t{item[1]}\n')
    f.close()
