## IPV4协议收发实验



### 实验目的

​	根据计算机网络实验系统所提供的上下层接口函数和协议中分组收发 的主要流程，设计实现一个简单的 IPv4 分组收发模块。

​	要求实现的主 要功能包括： 

​		1） IPv4 分组的基本接收处理；包括：检查目的地址是否为本地地址，并检查 IPv4 分组头部中其它字段的合法性。提交正确的分组给上层协议继续处理，丢弃错误的分组并说明错误类型

​		2） IPv4 分组的封装发送；包括：根据上层协议所提供的参数（存活时间、源地址、目标地址等）来填充，并计算校验和，封装 IPv4 分组，调用系统提供的发送接口函数将分组发送出去。

### 思考与方法

​	本次实验的主要难点在于对IPV4协议分组结构的正确认识，以及如何进行位运算等操作。容易出现的bug是：

		1. 字符串的长度/指向字符串的指针/字符串应该占的字节数的混淆
  		2. 大端法小端法的转换
  		3. checksum校验码的计算
  		4. 位运算操作的便捷性

​	**实现方法：**

​	由于协议头的结构特点，将其作为unsigned int类型读出，进行位运算修改或保存。

​	在发送实验中，根据上层协议所提供的参数（存活时间、源地址、目标地址等）来先设计分组头部，并计算得到校验和，再结合负载数据，得到完整的封装后的分组，如何然后进行发送。

​	在接收实验中，主要工作是提取分组头的信息，进行错误检验，并根据错误的不同类型进行汇报。

### 步骤

#### 发送实验：

1. 进行Version、IHL、Total length 等固定字段的填充
2. 根据上层协议信息，填写分组头的TTL、source address、destination address的填充
3. 计算checksum校验和并填充
4. 小端转大端
5. 封装数据并发送

#### 接收实验：

1. 得到分组头，转为小端法

2. 使用位运算，进行各种错误的检验：

    ​		STUD_IP_TEST_CHECKSUM_ERROR
    ​        STUD_IP_TEST_TTL_ERROR
    ​        STUD_IP_TEST_VERSION_ERROR
    ​        STUD_IP_TEST_HEADLEN_ERROR
    ​        STUD_IP_TEST_DESTINATION_ERROR

### 结果：

​	能够正确进行封装发送，并接收校验。

### 遇到的问题及总结

####  问题

​	一开始对位运算企图想保持pBuffer char*的形式，发现比较麻烦，于是改用unsigned int形式。

​	最后封装合并头部和报文时，一开始用for循环是正确的，使用memcpy报错，最终发现是 sizeof判断的是指针的大小，而非指向的字节数组的大小。最终使用数据真实大小来代替。

#### 总结

​	这次实验比较简单，但在写代码的过程中对IPV4协议格式有了更加深刻的印象，也认识到了实现过程中细节的重要性。

### 实现代码

```c++
#include "sysInclude.h"
#include <cstring>

extern void ip_DiscardPkt(char* pBuffer,int type);
extern void ip_SendtoLower(char*pBuffer,int length);
extern void ip_SendtoUp(char *pBuffer,int length);
extern unsigned int getIpv4Address();

/* 计算校验和 */
unsigned int getCheckSum(unsigned int* myHead)
{
    unsigned int checksum = 0;
    for(int i = 0; i < 5; i++)
    {
        checksum += (myHead[i] >> 16) + (myHead[i] & 0xffff);
    }
    checksum = (checksum >> 16) + (checksum & 0xffff);
    return (~checksum) & 0xffff;
}

/* 根据协议提取信息并进行检验，出错则返回错误信息 */
int myCheck(unsigned int *pBuffer)
{
    
    if((pBuffer[0]>>28) != 4)
        return STUD_IP_TEST_VERSION_ERROR;
    if(((pBuffer[0]>>24) & 0xf) < 5)
        return STUD_IP_TEST_HEADLEN_ERROR;
    if(((pBuffer[2]>>24) & 0xff) <= 0)
        return STUD_IP_TEST_TTL_ERROR;
    if(getCheckSum(pBuffer) != 0)
        return STUD_IP_TEST_CHECKSUM_ERROR;
    if(pBuffer[4] != getIpv4Address() && pBuffer[4] != getIpv4Address() | 0xffffff)
        return STUD_IP_TEST_DESTINATION_ERROR;
    return 0;
}

/* 接收分组并检验 */
int stud_ip_recv(char *pBuffer,unsigned short length)
{
    for(int i = 0; i < 5; i++)
    {
        (unsigned int*)pBuffer[i] = ntohl((unsigned int*)pBuffer[i]);
    }
    int type = myCheck((unsigned int*)pBuffer);
    switch (type)
    {
        case STUD_IP_TEST_CHECKSUM_ERROR:
        case STUD_IP_TEST_TTL_ERROR:
        case STUD_IP_TEST_VERSION_ERROR:
        case STUD_IP_TEST_HEADLEN_ERROR:
        case STUD_IP_TEST_DESTINATION_ERROR:
            ip_DiscardPkt(pBuffer, type);
            return 1;
            break;
        default:
            unsigned int headlen = ((unsigned int*)pBuffer[0]>>24) & 0xf;
            ip_SendtoUp(pBuffer + 4*headlen, (int)length - 4*headlen);
            return 0;
            break;
    }
	return 0;
}

/* 接收参数和数据进行封装并发送 */
int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
				   unsigned int dstAddr,byte protocol,byte ttl)
{
    unsigned int myHead[6] = {0};
    myHead[0] = (0x45 << 24) + 5*4 + len;
    myHead[1] = 0;
    myHead[2] = ((unsigned int)ttl << 24) + ((unsigned int)protocol << 16);
    myHead[3] = srcAddr;
    myHead[4] = dstAddr;
    unsigned int checksum = getCheckSum(myHead);
    
    myHead[2] += checksum;
    for(int i = 0; i < 5; i++)
    {
        myHead[i] = htonl(myHead[i]);
    }
    char myBuffer[65535];

    memcpy(myBuffer, (char *)myHead, sizeof(myHead));
    memcpy(myBuffer+20, pBuffer, strlen(pBuffer)+1);

    ip_SendtoLower(myBuffer, len + 20);
	return 0;
}

```

