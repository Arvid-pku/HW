## IPV4协议转发实验



### 实验目的

​	增加IPV4分组转发功能，对于每一个到达本机的 IPv4 分组，根据其目的 IPv4 地址决定分组的处理行为：

​		1) 向上层协议上交目的地址为本机地址的分组；

​		 2) 根据路由查找结果，丢弃查不到路由的分组； 

​		3) 根据路由查找结果，向相应接口转发不是本机接收的分组。

​	主要内容有：

​		1) 路由表数据结构的设计

​		2) 分组转发的行为处理，包括判断丢弃，寻找下一跳等

### 思考与方法

​	本次实验的主要难点在于路由表数据结构的设计，高效最大覆盖查找目标。容易出现的bug是：

1. 字符串的长度/指向字符串的指针/字符串应该占的字节数的混淆
2. message 大端法小端法的转换
3. 最大覆盖的解决
4. 位运算及其他运算的优先级



	#### 思考

关于路由表数据结构的选择，前后思考了以下几种方案：

1. 链表。不予评论

2. 二叉树，更快一些，但想思考一下其他方案

3. 哈希表/散列表，一开始打算用这个结构，进行了初步实现，效率很高。但突然发现要求最大覆盖进行匹配，于是需要改进。

4. 按覆盖长度32-1来做哈希表的数组，从最大长度来寻找匹配。但是发现：覆盖长度为1的与32的可能的子网的数量极度不匹配，于是糟糕的情况下会跟链表效率差不多。

5. 哈希后面散列的链表使用二叉树，感觉没必要

6. 希望找到一个可以保持地址单调性进行哈希的函数，然后将有掩码的地址表示的范围两端进行哈希。用双向链表保存地址串。寻找一个地址时，只需要向前找最接近的地址，就是最长覆盖的地址。如图：

    ​	  <img src="${mdImageFile}/image-20201129022057635.png" alt="image-20201129022057635" style="zoom:33%;" />

    但我发现，如果存在一个小于C但是大于B的一个地址，就需要向前进行顺序匹配查找，虽然不多，但也不方便。

    最后还是采用了二叉树，不过需要保存并更新最大匹配。。

关于下一跳就是最终目标的解决，即如果之前更新路由表，并未明确告诉(dest=nexthop, nexthop=nexthop, masklen=32)的情况，也应该知道自己可以到达下一跳的。有两种解决方案：

1. 维护一个下一跳的数组/哈希表，判断dest是否是下一跳

2. 更新(dest, nexthop, masklen)时，顺便更新(nexthop, nexthop, 32)

    选取了实现简单的第二种

#### 实现方法：

初始化二叉树，二叉树按大小顺序储存dest值，并保存可以到达dest的nexthop。

更新路由表就是插入二叉树结点，并且插入邻居自己到自己的结点。

寻找下一跳就是根据dest的值进行二叉树寻找。



### 步骤

1. 初始化二叉树
2. 更新路由表、插入树结点（包括下一跳自己到自己）
3. 大端转小端
4. 进行判断：TTL、自己接收
5. 进行二叉树查找
6. 根据查找结果丢弃/转发

### 结果：

​	能够正确并高效的进行转发、丢弃

### 遇到的问题及总结

#### 问题

​	主要问题就是数据结构的选择，最终选择了表现较好的二叉树，之后会再考虑哈希表的改善

​	其次是位运算的一些小bug：优先级，移位之后忘了移回

​	忘记邻居自己的masklen=32的更新、msg的大端法

#### 总结

	1. 细节很重要
 	2. 数据结构不只课堂上那些，可以根据应用去设计
 	3. 慢慢改善

### 实现代码

```c++
#include "sysInclude.h"

// system support
extern void fwd_LocalRcv(char *pBuffer, int length);
extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);
extern void fwd_DiscardPkt(char *pBuffer, int type);
extern unsigned int getIpv4Address( );

/* 二叉树结点 */
class Node
{
    public:
        Node *left;
        Node *right;
        stud_route_msg msg;
        Node()
        {
            left = NULL;
            right = NULL;
            msg.dest = 0;
            msg.nexthop = 0;
            msg.masklen = 0;
        }
        Node(stud_route_msg* mm)
        {
            left = NULL;
            right = NULL;
            msg.dest = mm->dest;
            msg.nexthop = mm->nexthop;
            msg.masklen = mm->masklen;
        }
};
Node *tree;

/* 二叉树查找 */
unsigned int foundDest(unsigned int dest)
{
    /* 最大匹配的地址 */
    unsigned int maxMatch = 0;
    Node *p = tree;
    while (p != NULL)
    {
        if(dest < p->msg.dest)
            p = p->left;
        else if(dest > p->msg.dest)
        {
            if ((unsigned int)(dest&(0xffffffff << (32-p->msg.masklen))) == p->msg.dest)
                maxMatch = p->msg.nexthop;
            p = p->right;
        }
        else
        {
            maxMatch = p->msg.nexthop;
            break;
        }
        
    }
    
    if(maxMatch == 0)
        return STUD_FORWARD_TEST_NOROUTE;
    else
        return maxMatch;
    
}
/* 校验和 */
unsigned int getCheckSum(unsigned int* myHead)
{
    unsigned int checksum = 0;
    for(int i = 0; i < 5; i++)
        checksum += (myHead[i] >> 16) + (myHead[i] & 0xffff);
    checksum = (checksum >> 16) + (checksum & 0xffff);
    return (~checksum) & 0xffff;
}

void stud_Route_Init()
{
	return;
}

/* 插入结点 */
void addNode(stud_route_msg *proute)
{
    if(tree == NULL)
        tree = new Node(proute);
    else
    {
        Node *p = tree;
        unsigned int dest = proute->dest;
        while(true)
        {
            if(dest > p->msg.dest)
            {
                if(p->right == NULL)
                {
                    p->right = new Node(proute);
                    break;
                }
                else
                    p = p->right;
            }
            if(dest < p->msg.dest)
            {
                if(p->left == NULL)
                {
                    p->left = new Node(proute);
                    break;
                }
                else
                    p = p->left;
            }
            if(dest == p->msg.dest)
            {
                p->msg.nexthop = proute->nexthop;
                break;
            }
        }
        
    }
}

/* 更新路由表 */
void stud_route_add(stud_route_msg *proute)
{
    proute->masklen = ntohl(proute->masklen);
    proute->nexthop = ntohl(proute->nexthop);
    proute->dest = ntohl(proute->dest);
    addNode(proute);
    proute->masklen = 32;
    proute->dest = proute->nexthop;
    addNode(proute);
	return;
}


int stud_fwd_deal(char *pBuffer, int length)
{
    unsigned int myBuffer[5];
    for(int i = 0; i < 5; i++)
        myBuffer[i] = ntohl(((unsigned int*)pBuffer)[i]);
	/* 自己 */
    if(myBuffer[4] == getIpv4Address() || (myBuffer[4] == (getIpv4Address() | 0xffffff)))
        fwd_LocalRcv(pBuffer, length);
    else
    {
        /* 没有下一跳 */
        unsigned int next = foundDest(myBuffer[4]);
        if(next==STUD_FORWARD_TEST_NOROUTE)
        {
            fwd_DiscardPkt(pBuffer, next);
            return 1;
        }
        else
        {
            /* 超时 */
            unsigned int ttl = myBuffer[2] >> 24;
            if(ttl <= 0)
            {
                fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
                return 1;
            }
            else
            {
                /* 转发 */
                ttl--;
                myBuffer[2] = (myBuffer[2] & 0xff0000) + (ttl << 24);
                myBuffer[2] = getCheckSum(myBuffer) + myBuffer[2];
                ((unsigned int*)pBuffer)[2] = htonl(myBuffer[2]);
                fwd_SendtoLower(pBuffer, length, next);
            }
        }
    }
	return 0;
}


```