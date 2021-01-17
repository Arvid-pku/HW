import json
import re

titleP = re.compile('<title>(.+?)</title>') # 找到标题
retitleP = re.compile('<redirect title="(.+?)" />') # 找到重定向
outlinkP = re.compile('\[\[([^\[\]]*)\]\](\w*)')  # 找到链接

cantin = False # 此页面是否可取
redict = {} # 重定向的名字
redict['Book sources'] = 'Book sources' # 两个特殊情况
redict['Special:BookSources'] = 'Book sources'

graph = {} # 最后的出边字典


# 特殊情况
def rarepro(line, nowlinks):
    if "{{ISBN" in line:
        nowlinks.add('International Standard Book Number')
        nowlinks.add('Book sources')
    if "{{IPAc" in line:
        nowlinks.add('Help:IPA')
    return nowlinks


# 更新添加结点和边
def myupdate(nowtitle, nowlinks):
    global graph
    global redict
    if nowtitle in graph.keys():
        graph[nowtitle] = graph[nowtitle] + list(nowlinks)
    else:
        graph[nowtitle] = list(nowlinks)
    mylen = len(graph)
    if mylen % 10000 == 0:
        print(mylen)

    # 完成任务
    if  mylen > 1000050:
        oldlen = 0
        while len(graph) != oldlen:
            oldlen = len(graph)
            for item in graph.items():
                # 删去不是结点的边
                tmp = list(map(lambda x: redict[x], list(filter(lambda x: x in redict.keys(), item[1]))))
                graph[item[0]] = list(filter(lambda x: x != item[0], tmp))
            for item in graph.items():
                graph[item[0]] = list(filter(lambda x: x in graph.keys(), item[1]))
        if len(graph) > 1000000:
            return True
    return False

# 特殊情况   
def tocat(x):
    return x.split(':')[0] != 'Category' or x[0] == ':'

# 产生图
with open('../datawiki/enwiki-20180920-pages-articles-multistream.xml', 'r') as f:
    nowtitle = ''
    nowlinks = set()
    for line in f:
        title = titleP.findall(line)
        retitle = retitleP.findall(line)
        outlink = set(map(lambda x: x[0]+x[1], outlinkP.findall(line)))
        nowlinks = rarepro(line, nowlinks)
        
        # 进行处理
        if title:
            if nowtitle:
                if not cantin:
                    if myupdate(nowtitle, nowlinks):
                        break
                nowlinks = set()
                cantin = False
            # 去掉特殊的情况，标准式。如果想要链接式，注释下方两行
            if 'Wikipedia:' in title[0] or 'Help:' in title[0] or 'Category:' in title[0]:
                cantin = True
            nowtitle = title[0]
        if retitle:
            cantin = True
            redict[nowtitle] = retitle[0]
            nowtitle = retitle[0]
            redict[nowtitle] = nowtitle
        if outlink:
            # 一些规则
            outlink = set(filter(lambda x: x!= nowtitle and tocat(x) and x and x!= ':', set(map(lambda x: x.split('|')[0].split('#')[0].split('/')[0], outlink))))
            try:
                outlink = set(map(lambda x: x[1].upper()+x[2:] if x[0]==':' else x[0].upper()+x[1:], outlink))
            except IndexError:
                print(outlink)
            nowlinks = nowlinks|outlink



# 存图
with open('graph.json', 'w') as f:
    json.dump(graph, f, indent=4)