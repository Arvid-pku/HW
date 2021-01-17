## TCP 协议实验


### 实验目的

实现客户端角色的、“停－等” 模式的 TCP 协议，能够正确的建立和拆除连接，接
收和发送 TCP 报文，并向应用层提供客户端需要的 Socket 函数。

具体来说，主要包括：

1. 设计保存 TCP 连接相关信息的数据结构 TCB。
2. TCP 协议的接收处理。实现 stud_tcp_input( )函数，完成检查校验和、字节序转
    换功能（对头部中的选项不做处理），实现客户端角色的 TCP 报文接收的有限状态机。
3. TCP 协议的封装发送。实现 stud_tcp_output( )函数，完成简单的 TCP 协议的封
    装发送功能，在收到对上一个报文的确认后继续发送。
4. 提供 Socket 函数接口，实现与客户端角色的 TCP 协议相关的 5 个 Socket 接口函数，
    stud_tcp_socket( )、stud_tcp_connect ( )、stud_tcp_recv ( )、
    stud_tcp_send ( )和 stud_tcp_close ( )。

### 思考

#### 主要理解

​	首先需要理解  stud_tcp_input( ) 、stud_tcp_output( ) 函数与另外几个Socket函数接口的区别与联系：input与output是受系统/socket接口调用的、实现客户端与服务器直接联系的函数；而socket接口这些函数是受系统调用的，与应用层之间联系的一些接口。主要关系如下图所示：

​		<img src="${mdImageFile}/image-20201207233205159.png" alt="image-20201207233205159" style="zoom: 50%;" />					

​	而TCP协议是一个记录状态的协议，每个TCB结构（或者说连接）都有下图中的状态，而这些状态需要在系统调用input、output和socket接口时进行转移。状态过程主要是三次握手、四次挥手以及中间的数据传输部分。

<img src="${mdImageFile}/image-20201207233139500.png" alt="image-20201207233139500" style="zoom: 50%;" />

​	此外，TCP包的收发也有一些知识需要注意：

1. TCP 中序列号和确认号机制：TCB的序列号和确认号每次需要按照规则进行更新：序列号等于发来包的确认号，确认号等于发来包的序列号加上数据的长度，SYN等信号是加一。
2. TCP 计算校验和：需要计算配置一个伪头。当有数据时需要连数据也进行校验。
3. TCP flag：根据flag来判断信号种类，并需要进行设置。
4. TCB 链表结构：多个连接时需要根据 sockfd来标识不同的TCB，建立链表进行管理。

#### 实现要点

​	实验中实现的重点是：

1. 接收与封装**tcp包**时的属性的提取与更改
2. 接收tcp包的**校验**和检查
3. 根据当下状态和接收信号来进行相应TCB**状态的转移**
4. TCB以及发送包的**ack和seq号**的计算更新
5. TCB连接的**链表**的建立与管理
6. 注意主机与网络**字节序**，如stud_tcp_output() 是主机字节序。

### 方法步骤

1. 实现 stud_tcp_input() ：
    1. 提取收到的tcp包的信息，进行格式转换。
    2. 进行检查：
        1. 检查校验和，注意伪头与数据。
        2. 字节序转换。
        3. 检查序列号。
    3.  状态转移
        1. 输入有限状态机处理，根据当下状态与信号更改状态，并且有必要的话调用stud_tcp_output() 来向服务器返回信号。
2. 实现stud_tcp_output():
    1. 封装tcp包
        1. 根据收到的数据，计算校验和等，封装成tcp包
    2. 根据信号和状态进行状态转移
    3. 进行字节序的转换和调用sendIpPkt( )发送
3. 实现socket 接口：
    1. stud_tcp_socket() 建立对应的TCB，加入链表，返回对应的sockfd
    2. stud_tcp_connect() 完善建好的TCB的端口号地址等信息，与对应服务器进行三次握手
    3. stud_tcp_send ( ) 判断ESTABLISHED 状态，将数据拷贝到缓冲区调用 stud_tcp_output ( )发送。
    4. stud_tcp_recv ( ) 判断 ESTABLISHED 状态，从 TCB 的输入缓冲区读出数据，交给应用层协议。
    5. stud_tcp_close ( ) 根据状态和TCB寻找情况，若有异常，删除退出。正常情况下，进行四次挥手。



### 结果：

​	通过所有测试，序列号等包信息正确发送与接收。

### 遇到的问题及总结

#### 遇到的问题

 1. 一开始不理解input、output与socket接口的区别与联系，误认为功能重叠，进一步理解才明白调用和层次关系。

 2. 实验中一些信号和状态转移与参考书和课本上不符，根据分析包进行了调整

 3. tcp的校验计算、确认号、序列号的更新等规则进行了巩固与学习

 4. 一些字节序和位运算取值等的错误以及debug

 5. close时链表的删除过早导致后面不能进行握手

    

#### 总结

1. 进一步加深了对TCP协议细节的理解，以及对层次的理解
2. 更加熟练的使用了平台的调试与包分析的功能，前面实验几乎没用到
3. 实验参考书中的出入也较好的锻炼了心态和debug随机应变的能力（x
4. 本次实验比前几个花了更多的时间，收获也更多。同时也感到，设计TCP等协议的那些前辈们实现了怎样宏大的工程！





### 实现代码

```c++
#include "sysInclude.h"
#include <cstring>
extern void tcp_DiscardPkt(char *pBuffer, int type);

extern void tcp_sendReport(int type);

extern void tcp_sendIpPkt(unsigned char *pData, UINT16 len, unsigned int  srcAddr, unsigned int dstAddr, UINT8	ttl);

extern int waitIpPacket(char *pBuffer, int timeout);

extern unsigned int getIpv4Address();

extern unsigned int getServerIpv4Address();

enum STATE {CLOSED, SYNSENT, ESTABLISHED, FINWAIT1, FINWAIT2, TIMEWAIT};

short gSrcPort = 2006;
int gSeqNum = 1;
int gAckNum = 0;

/* TCB 结构单元 */
struct TCB
{
    int sockfd;
    unsigned int srcAddr;
    unsigned int dstAddr;
    unsigned short srcPort;
    unsigned short dstPort;
    unsigned int seq;
    unsigned int ack;
    STATE state;
    TCB* next;
    TCB(int fd = 0)
    {
        sockfd = fd;
        srcAddr = 0;
        dstAddr = 0;
        srcPort = 0;
        dstPort = 0;
        state = CLOSED;
        seq = gSeqNum;
        ack = gAckNum;
        next = NULL;
    }
};


/* TCB 链表头 */
TCB *TCBlink = NULL;
int sockFd = 1;
unsigned int timeout = 5;
int buffersize = 1024;

/* 进行flag的识别与转换：位表示与char类型表示 */
unsigned short flag2num(char flag)
{
    unsigned short num = 0;
    switch (flag)
    {
    case PACKET_TYPE_SYN:
        num = 0x2; break;
    case PACKET_TYPE_SYN_ACK:
        num = 0x12; break;
    case PACKET_TYPE_ACK:
        num = 0x10; break;
    case PACKET_TYPE_FIN:
        num = 0x1; break;
    case PACKET_TYPE_FIN_ACK:
        num = 0x11; break;
    default: break;
    }
    return num;
}
char num2flag(unsigned short num)
{
    char flag = PACKET_TYPE_DATA;
    switch (num)
    {
    case 0x2:
        flag = PACKET_TYPE_SYN; break;
    case 0x12:
        flag = PACKET_TYPE_SYN_ACK; break;
    case 0x10:
        flag = PACKET_TYPE_ACK; break;
    case 0x1:
        flag = PACKET_TYPE_FIN; break;
    case 0x11:
        flag = PACKET_TYPE_FIN_ACK; break;
    default: break;
    }
    return flag;
}

/* 进行常用的校验和的计算 */
unsigned int getChecksum(unsigned int* pBuffer)
{
    unsigned int checksum = 0;
    for(int i = 0; i < 15; i++)
        checksum += (pBuffer[i] >> 16) + (pBuffer[i] & 0xffff);
    return (~((checksum >> 16) + (checksum & 0xffff))) & 0xffff;
}
/* 根据目标地址或sockfd两种寻找TCB的方法 */
TCB* getTCB(unsigned int dstAddr, unsigned short dstPost)
{
    TCB* nowtcb = TCBlink;
    while (nowtcb != NULL && (nowtcb->dstAddr != dstAddr || nowtcb->dstPort != dstPost))
        nowtcb = nowtcb->next;
    return nowtcb;
}
TCB* findTCB(int sockfd)
{
    TCB* nowtcb = TCBlink;
    while (nowtcb!=NULL && nowtcb->sockfd!=sockfd)
        nowtcb = nowtcb->next;
    return nowtcb;
}
/* 常用的设置序列号和确认号的方法 */
void setSeqAck(TCB* tcb, char* buffer)
{
    tcb->seq = ntohl(*(unsigned int*)(buffer+8));
    tcb->ack = ntohl(*(unsigned int*)(buffer+4)) + 1;
}
/* stud_tcp_input() 函数，主要功能在前面报告已经叙述 */
int stud_tcp_input(char *pBuffer, unsigned short len, unsigned int srcAddr, unsigned int dstAddr)
{
    /* 得到伪头+TCP头+数据*/
    unsigned int myBuffer[15] = {0};
    myBuffer[0] = ntohl(srcAddr);
    myBuffer[1] = ntohl(dstAddr);
    myBuffer[2] = (6 << 16) + (len);
    for(int i = 3; i < 8; i++)
        myBuffer[i] = ntohl(((unsigned int*)pBuffer)[i-3]);
    unsigned short srcPort = (myBuffer[3]>>16) & 0xffff;
    unsigned short dstPort = myBuffer[3] & 0xffff;
    unsigned int seqnum = myBuffer[4];
    unsigned int acknum = myBuffer[5];
    unsigned short flag = (unsigned short)((myBuffer[6] >> 16) & 0x3f);
    /* 校验和 */
    if (getChecksum(myBuffer) != 0 || myBuffer[1] != getIpv4Address())
        return -1;
    TCB* tcb = getTCB(myBuffer[0], srcPort);
    if(tcb == NULL)
        return -1;
    if(acknum != tcb->seq + 1)
    {
        tcp_DiscardPkt(pBuffer, STUD_TCP_TEST_SEQNO_ERROR);
        return -1;
    }
    /* 状态转换及信号发送 */
    if(tcb->state == SYNSENT && num2flag(flag) == PACKET_TYPE_SYN_ACK)
    {
        tcb->seq = acknum;
        tcb->ack = seqnum + 1;
        stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, tcb->srcPort, tcb->dstPort, tcb->srcAddr, tcb->dstAddr);
        tcb->state = ESTABLISHED;
    }
    else if(tcb->state == FINWAIT1 && num2flag(flag) == PACKET_TYPE_ACK)
        tcb->state = FINWAIT2;
    else if(tcb->state == FINWAIT2 && num2flag(flag) == PACKET_TYPE_FIN_ACK)
    {
        tcb->seq = acknum;
        tcb->ack = seqnum + 1;
        tcb->state = TIMEWAIT;
        stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, tcb->srcPort, tcb->dstPort, tcb->srcAddr, tcb->dstAddr);
        tcb->state = CLOSED;
    }
    else
        return -1;
	return 0;
}

/* stud_tcp_output 函数，进行封装与发送+状态转移 */
void stud_tcp_output(char *pData, unsigned short len, unsigned char flag, unsigned short srcPort, unsigned short dstPort, unsigned int srcAddr, unsigned int dstAddr)
{
    TCB *tcb = getTCB(dstAddr, dstPort);
    if(TCBlink == NULL)
    {
        tcb = new TCB(sockFd++);
        TCBlink = tcb;
        tcb->dstAddr = dstAddr;
        tcb->dstPort = dstPort;
        tcb->srcAddr = srcAddr;
        tcb->srcPort = srcPort;
        tcb->state = CLOSED;
        tcb->ack = 0;
        tcb->seq = 1;
    }
    if(tcb == NULL)
        return;
    unsigned int myBuffer[15] = {0};
    myBuffer[0] = srcAddr;
    myBuffer[1] = dstAddr;
    myBuffer[2] = (6 << 16) + (20+len);
    myBuffer[3] = (((unsigned int)srcPort) << 16) + ((unsigned int)dstPort);
    myBuffer[4] = tcb->seq;
    myBuffer[5] = tcb->ack;
    myBuffer[6] = (5 << 28) + (((unsigned int)flag2num(flag)) << 16);
    if(flag == PACKET_TYPE_SYN)
        tcb->state = SYNSENT;
    else if(flag == PACKET_TYPE_FIN_ACK)
        tcb->state = FINWAIT1;
    memcpy(myBuffer+8, (unsigned int*)pData, len);
    for(int i = 8; i < 15; i++)
        myBuffer[i] = htonl(myBuffer[i]);
    unsigned int checksum = getChecksum(myBuffer);
    myBuffer[7] = (checksum << 16);
    for(int i = 3; i < 15; i++)
        myBuffer[i] = htonl(myBuffer[i]);
    unsigned short ttl = 5;
    tcp_sendIpPkt((unsigned char*)(myBuffer+3), len+20, srcAddr, dstAddr, ttl);
    return;
}
/* 建立TCB，状态是CLOSED */
int stud_tcp_socket(int domain, int type, int protocol)
{
    TCB* tcb = new TCB(sockFd);
    sockFd += 1;
    tcb->next = TCBlink;
    TCBlink = tcb;
	return TCBlink->sockfd;
}
/* 进行握手，建立连接 */
int stud_tcp_connect(int sockfd, struct sockaddr_in *addr, int addrlen)
{
    TCB* nowtcb = findTCB(sockfd);
    if(nowtcb == NULL)
        return -1;
    nowtcb->srcAddr = getIpv4Address();
    nowtcb->srcPort = gSrcPort;
    nowtcb->dstAddr = ntohl(addr->sin_addr.s_addr);
    nowtcb->dstPort = ntohs(addr->sin_port);
    stud_tcp_output(NULL, 0, PACKET_TYPE_SYN, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
    char buffer[buffersize];
    if (waitIpPacket(buffer, timeout) == -1)
        return -1;
    setSeqAck(nowtcb, buffer);
    stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
    nowtcb->state = ESTABLISHED;
    return 0;
}
/* 发送包，等的回复ack */
int stud_tcp_send(int sockfd, const unsigned char *pData, unsigned short datalen, int flags)
{
    TCB* nowtcb = findTCB(sockfd);
    if(nowtcb == NULL || nowtcb->state!=ESTABLISHED)
        return -1;
    stud_tcp_output((char*)pData, datalen, PACKET_TYPE_DATA, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
    char buffer[buffersize];
    if(waitIpPacket(buffer, timeout) == -1 || (buffer[13]&0x13)!=0x10)
        return -1;
    setSeqAck(nowtcb, buffer);
	return 0;
}
/* 主动接收包，并回复ACK */
int stud_tcp_recv(int sockfd, unsigned char *pData, unsigned short datalen, int flags)
{
    TCB* nowtcb = findTCB(sockfd);
    if(nowtcb == NULL || nowtcb->state != ESTABLISHED)
        return -1;
    char buffer[buffersize];
    int len = waitIpPacket(buffer, timeout);
    if(len == -1) return -1;
    int header_length = (buffer[12]>>2) & 0x3c;
    memcpy(pData, buffer+header_length, len-header_length);
    setSeqAck(nowtcb, buffer);
    if(len - 20 > 0)
        nowtcb->ack += len - 21;
    else if((buffer[13]&0x13)==0x10)
        nowtcb->ack -= 1;
    stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
	return 0;
}
/* 挥手关闭连接 */
int stud_tcp_close(int sockfd)
{
    TCB *pretcb = NULL;
    TCB *nowtcb = TCBlink;
    while (nowtcb != NULL && nowtcb->sockfd != sockfd)
    {
        pretcb = nowtcb;
        nowtcb = nowtcb->next;
    }
    /* 异常处理*/
    if(nowtcb == NULL)
        return -1;
    if(nowtcb->state != ESTABLISHED)
    {
        delete nowtcb;
        return -1;
    }
    /* 正常挥手 */
    else
    {
        stud_tcp_output(NULL, 0, PACKET_TYPE_FIN_ACK, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
        char buffer[buffersize];
        memset(buffer, 0, sizeof(buffer));
        if(waitIpPacket(buffer, timeout) == -1 || (buffer[13]&0x13) != 0x10)
            return -1;
        nowtcb->state = FINWAIT2;
        setSeqAck(nowtcb, buffer);
        
        if(waitIpPacket(buffer, timeout) == -1 || (buffer[13]&0x13) != 0x11)
            return -1;
        nowtcb->state = TIMEWAIT;
        setSeqAck(nowtcb, buffer);
        stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
    }
    /* 从链表移除 */
    if(pretcb == NULL)
        TCBlink = TCBlink->next;
    else
        pretcb->next = nowtcb->next;
    
    delete nowtcb;
	return 0;
}


```