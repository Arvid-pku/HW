## 计算机网络概论-第一次实验



### 实验流程

#### 1. 停等式协议

停等式协议较为简单，窗口大小为1。

* 收到MSG_TYPE_SEND信号后，将pBuffer指向的数据帧缓存到队列尾部，排队准备发送。若此时窗口为空，可以发送，那就发送队首的数据帧。
* 收到MSG_TYPE_RECEIVE信号后，将队首数据帧移除，查看缓冲队列，如果不为空，发送下一个帧。
* 收到MSG_TYPE_TIMEOUT信号后，再次发送队首的数据帧。

定义的变量：

* window：true表示空闲，可以发送下一个，false表示占用中
* mybuf：用来缓存pBuffer指向的数据帧（如果有的话）
* mybufpro：用来缓存mybuf和对应的buffersize
* toSend：缓存的队列

主要代码如下：

```python
int stud_slide_window_stop_and_wait(char *pBuffer, int bufferSize, UINT8 messageType)
{
    // 用来缓存pBuffer指向的数据帧，数据不管有没有发送只要没确认收到都存在toSend里面
    myframe mybuf;
    framepro mybufpro;

    // 如果信号是SEND，把pBuffer缓存，如果可以发送，发送之
    if(messageType == MSG_TYPE_SEND)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        toSend.push(mybufpro);
        if(window)
        {
            window = false;
            SendFRAMEPacket((unsigned char*)&mybuf, mybufpro.framesize);
        }
    }
    // 如果信号是RECEIVE，更改windows，允许发送，如果等待队列有数据帧，发送之
    else if(messageType == MSG_TYPE_RECEIVE)
    {
        toSend.pop();
        if(toSend.empty())
            window = true;
        else
        {
            window = false;
            SendFRAMEPacket((unsigned char*)&toSend.front().frame, toSend.front().framesize);
        }
    }

    // 如果信号是TIMEOUT，重新发送队首的数据帧
    else if(messageType == MSG_TYPE_TIMEOUT)
        SendFRAMEPacket((unsigned char*)&toSend.front().frame, toSend.front().framesize);
    else
        return -1;
	return 0;
}

```



#### 2. 回退N帧协议

回退N帧协议在停等协议的基础上，窗口大小变为4。

于是设计两个队列来模拟缓冲区，一个队列alreadySend，最大长度为4，保存已经发送等待确认的数据帧。它的大小便是窗口的概念。另一个队列toSend，储存等待发送的帧。

* 收到MSG_TYPE_SEND信号后，将pBuffer指向的数据帧缓存到队列尾部，排队准备发送。若此时窗口有空（即alreadySend大小小于4），可以发送几个数据帧，那就发送toSend队首的几个数据帧，并将它们存储在alreadySend里面。
* 收到MSG_TYPE_RECEIVE信号后，查看收到数据帧的ack，并在alreadySend里面找到对应的数据帧（需要进行大小端法转换），将此帧及前面的帧移除（已经确认），并结合缓冲队列数据帧的数目，再次发送一定数目的数据帧（min{notsend，emptywindow}。
* 收到MSG_TYPE_TIMEOUT信号后，将alreadySend窗口的数据帧全部重发一遍。

定义的变量：

* mybuf：用来缓存pBuffer指向的数据帧（如果有的话）
* mybufpro：用来缓存mybuf和对应的buffersize
* toSend：缓存的队列（未发送过）
* alreadySend：已经发送过但未确认的队列
* mysend函数：用来将toSend队列队首进行发送，并pop到alreadySend。

实现代码：

```python
// 回退N帧和选择性重传时方便发送
// alreadySend 队列保存已经发送未确认的数据帧，toSend保存未发送过的数据帧
void mysend()
{
    framepro mybufpro = toSend.front();
    alreadySend.push(mybufpro);
    toSend.pop();
    SendFRAMEPacket((unsigned char*)&mybufpro.frame, mybufpro.framesize);
}


/*
* 回退n帧测试函数
*/
int stud_slide_window_back_n_frame(char *pBuffer, int bufferSize, UINT8 messageType)
{
	myframe mybuf;
    framepro mybufpro;

    // SEND信号始终保持窗口满 or 无数据可发送
    if(messageType == MSG_TYPE_SEND)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        toSend.push(mybufpro);
        while(alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME && !toSend.empty())
        {
            mysend();
        }
    }

    // RECEIVE信号 接收ack，在已经发送的队列中找到seq==ack的数据帧，此帧与前面的帧都确认收到了
    // 然后补满窗口
    else if(messageType == MSG_TYPE_RECEIVE)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        while(ntohl(alreadySend.front().frame.head.seq) != ntohl(mybufpro.frame.head.ack))
        {
            alreadySend.pop();
        }
        alreadySend.pop();
        while(!toSend.empty() && alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME)
        {
            mysend();
        }
    }

    // TIMEOUT 信号，需要将窗口里面的数据帧全都发送一遍
    else if(messageType == MSG_TYPE_TIMEOUT)
    {
        unsigned int timeoutnum = (unsigned int)*pBuffer;
        bool needback = true;
        queue<framepro> tmp_queue;


        while(!alreadySend.empty())
        {
            mybufpro = alreadySend.front();
            if(ntohl(mybufpro.frame.head.seq) == timeoutnum || needback)
            {
                //cout << ntohl(mybufpro.frame.head.seq) << endl;
                SendFRAMEPacket((unsigned char*)&mybufpro.frame, mybufpro.framesize);
                needback = true;
                tmp_queue.push(mybufpro);
            }
            alreadySend.pop();
        }
        while(!tmp_queue.empty())
        {
            alreadySend.push(tmp_queue.front());
            tmp_queue.pop(); 
        }
        
        //alreadySend = tmp_queue;
    }
    else
        return -1;
	return 0;
}
```



#### 3. 选择重传协议

选择重传协议在回退N帧协议的基础上，增加对nak类型返回帧的处理，去掉MSG_TYPE_TIMEOUT信号。

alreadySend和toSend定义与之前一样。

* 收到MSG_TYPE_SEND信号后，将pBuffer指向的数据帧缓存到队列尾部，排队准备发送。若此时窗口有空（即alreadySend大小小于4），可以发送几个数据帧，那就发送toSend队首的几个数据帧，并将它们存储在alreadySend里面。（与回退N帧一致）
* 收到MSG_TYPE_RECEIVE信号后，查看收到的数据帧，在alreadySend里面找到对应的数据帧（需要进行大小端法转换），将前面的帧移除（已经确认），判断此帧，如果是ack，将其也移除；如果是nak，那就将其重发。之后结合缓冲队列数据帧的数目，再次发送一定数目的数据帧；（min{notsend，emptywindow}。

定义的变量（与回退N帧相同）：

* mybuf：用来缓存pBuffer指向的数据帧（如果有的话）
* mybufpro：用来缓存mybuf和对应的buffersize
* toSend：缓存的队列（未发送过）
* alreadySend：已经发送过但未确认的队列
* mysend函数：用来将toSend队列队首进行发送，并pop到alreadySend。

实现代码：

```python
/*
* 选择性重传测试函数
*/
int stud_slide_window_choice_frame_resend(char *pBuffer, int bufferSize, UINT8 messageType)
{
    myframe mybuf;
    framepro mybufpro;

    // SEND信号处理与回退N帧一样
    if(messageType == MSG_TYPE_SEND)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        toSend.push(mybufpro);
        while(alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME && !toSend.empty())
            mysend();
    }

    // RECEIVE 信号分为ack和nak，取决于是否需要重发
    else if(messageType == MSG_TYPE_RECEIVE)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        frame_kind mykind = mybufpro.frame.head.kind;
        while(ntohl(alreadySend.front().frame.head.seq) != ntohl(mybufpro.frame.head.ack))
            alreadySend.pop();
        if(mykind == htonl(ack))
            alreadySend.pop();
        else
            SendFRAMEPacket((unsigned char*)&alreadySend.front().frame, alreadySend.front().framesize);
        while(!toSend.empty() && alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME)
            mysend();
    }
    else
        return -1;
	return 0;
}

```







### 实验中的问题与想法

问题：

1. 一开始没有区分大小端法，debug好长时间才发现，一直以为是原理问题。
2. 在停等协议测试中，一开始没有区分数据帧的大小和传送数据的大小，导致数据帧传送长度不对。
3. 在回退N帧协议中，一开始没有判断ack的序号，下意识以为是一个一个确认的。确认序号之后，一开始以为ack值表示小于ack的数据帧都接收了，最后发现是小于等于ack的数据帧都接收。
4. 在回退N帧协议中，不知道为什么timeout序号是3，窗口是1， 2， 3，4时，仍然需要全部重新发送1， 2， 3，4。这样才能过，耽误了很长时间。
5. 选择重传中，再次忘记大小端法。



想法：

1. 从停等协议中构建好框架思维后，后面的结构都不难实现。主要是一些细节，和采取的定义（比如ack的意义，timeout重传的范围等）
2. 从回退N帧中想到用两个队列比较方便，选择重传本来打算用一个方面直接索引的dict或者vector，最后还是用普通的queue实现了。
3. 亲自动手实现这些协议，加深了理解，变得真切可见。



附：完整代码：

```python
#include "sysinclude.h"
#include <string.h>
#include <stdlib.h>
#include <queue>
#include <iostream>
extern void SendFRAMEPacket(unsigned char* pData, unsigned int len);

#define WINDOW_SIZE_STOP_WAIT 1
#define WINDOW_SIZE_BACK_N_FRAME 4

/*
* 停等协议测试函数
*/
typedef enum {data,ack,nak} frame_kind;

// 在本文件定义相关结构体，方便调用
typedef struct frame_head
{
    frame_kind kind;
    unsigned int seq;
    unsigned int ack;
    unsigned char data[100];
}myframe_head;
typedef struct frame
{
    myframe_head head;
    unsigned int size;
}myframe;

// 自定义结构体，用来保存 pBuffer 对应的 buffersize
typedef struct frame2
{
    myframe frame;
    unsigned int framesize;
}framepro;

// 两个队列，在三个实验中有具体的用途
static queue<framepro> toSend;
static queue<framepro> alreadySend;

// 判断停等实验中是否可以发送
static bool window = true;


int stud_slide_window_stop_and_wait(char *pBuffer, int bufferSize, UINT8 messageType)
{
    // 用来缓存pBuffer指向的数据帧，数据不管有没有发送只要没确认收到都存在toSend里面
    myframe mybuf;
    framepro mybufpro;

    // 如果信号是SEND，把pBuffer缓存，如果可以发送，发送之
    if(messageType == MSG_TYPE_SEND)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        toSend.push(mybufpro);
        if(window)
        {
            window = false;
            SendFRAMEPacket((unsigned char*)&mybuf, mybufpro.framesize);
        }
    }
    // 如果信号是RECEIVE，更改windows，允许发送，如果等待队列有数据帧，发送之
    else if(messageType == MSG_TYPE_RECEIVE)
    {
        toSend.pop();
        if(toSend.empty())
        {
            window = true;
        }
        else
        {
            window = false;
            SendFRAMEPacket((unsigned char*)&toSend.front().frame, toSend.front().framesize);
        }
    }

    // 如果信号是TIMEOUT，重新发送队首的数据帧
    else if(messageType == MSG_TYPE_TIMEOUT)
    {
        window = false;
        SendFRAMEPacket((unsigned char*)&toSend.front().frame, toSend.front().framesize);
    }
    else
    {
        return -1;
    }
	return 0;
}


// 回退N帧和选择性重传时方便发送
// alreadySend 队列保存已经发送未确认的数据帧，toSend保存未发送过的数据帧
void mysend()
{
    framepro mybufpro = toSend.front();
    alreadySend.push(mybufpro);
    toSend.pop();
    SendFRAMEPacket((unsigned char*)&mybufpro.frame, mybufpro.framesize);
}


/*
* 回退n帧测试函数
*/
int stud_slide_window_back_n_frame(char *pBuffer, int bufferSize, UINT8 messageType)
{
	myframe mybuf;
    framepro mybufpro;

    // SEND信号始终保持窗口满 or 无数据可发送
    if(messageType == MSG_TYPE_SEND)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        toSend.push(mybufpro);
        while(alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME && !toSend.empty())
        {
            mysend();
        }
    }

    // RECEIVE信号 接收ack，在已经发送的队列中找到seq==ack的数据帧，此帧与前面的帧都确认收到了
    // 然后补满窗口
    else if(messageType == MSG_TYPE_RECEIVE)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        while(ntohl(alreadySend.front().frame.head.seq) != ntohl(mybufpro.frame.head.ack))
        {
            alreadySend.pop();
        }
        alreadySend.pop();
        while(!toSend.empty() && alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME)
        {
            mysend();
        }
    }

    // TIMEOUT 信号，需要将窗口里面的数据帧全都发送一遍
    else if(messageType == MSG_TYPE_TIMEOUT)
    {
        unsigned int timeoutnum = (unsigned int)*pBuffer;
        bool needback = true;
        queue<framepro> tmp_queue;


        while(!alreadySend.empty())
        {
            mybufpro = alreadySend.front();
            if(ntohl(mybufpro.frame.head.seq) == timeoutnum || needback)
            {
                //cout << ntohl(mybufpro.frame.head.seq) << endl;
                SendFRAMEPacket((unsigned char*)&mybufpro.frame, mybufpro.framesize);
                needback = true;
                tmp_queue.push(mybufpro);
            }
            alreadySend.pop();
        }
        while(!tmp_queue.empty())
        {
            alreadySend.push(tmp_queue.front());
            tmp_queue.pop(); 
        }
        
        //alreadySend = tmp_queue;
    }
    else
    {
        return -1;
    }
	return 0;
}

/*
* 选择性重传测试函数
*/
int stud_slide_window_choice_frame_resend(char *pBuffer, int bufferSize, UINT8 messageType)
{
    myframe mybuf;
    framepro mybufpro;

    // SEND信号处理与回退N帧一样
    if(messageType == MSG_TYPE_SEND)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        toSend.push(mybufpro);
        while(alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME && !toSend.empty())
        {
            mysend();
        }
    }

    // RECEIVE 信号分为ack和nak，取决于是否需要重发
    else if(messageType == MSG_TYPE_RECEIVE)
    {
        memcpy(&mybuf, pBuffer, sizeof(myframe));
        mybufpro.framesize = bufferSize;
        mybufpro.frame = mybuf;
        frame_kind mykind = mybufpro.frame.head.kind;
        while(ntohl(alreadySend.front().frame.head.seq) != ntohl(mybufpro.frame.head.ack))
        {
            alreadySend.pop();
        }
        if(mykind == htonl(ack))
        {
            alreadySend.pop();
        }
        else
        {
            SendFRAMEPacket((unsigned char*)&alreadySend.front().frame, alreadySend.front().framesize);
        }
        while(!toSend.empty() && alreadySend.size() < WINDOW_SIZE_BACK_N_FRAME)
        {
            mysend();
        }
    }
    else
    {
        return -1;
    }
	return 0;
}

```











