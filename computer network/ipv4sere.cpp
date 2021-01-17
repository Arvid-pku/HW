/*
* THIS FILE IS FOR IP TEST
*/
// system support
#include "sysInclude.h"
#include <cstring>
#include <algorithm>
extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer,int length);

extern unsigned int getIpv4Address();

// implemented by students


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

    char *charHead = (char *)myHead;
    for(int i = 0; i < 20; i++)
    {
        myBuffer[i] = charHead[i];
    }
    for(int i = 20; i < 20+len; i++)
    {
        myBuffer[i] = pBuffer[i-20];
    }

    memcpy(myBuffer, (char *)myHead, sizeof(myHead));
    memcpy(myBuffer+20, pBuffer, strlen(pBuffer)+1);

    ip_SendtoLower(myBuffer, len + 20);
	return 0;
}
