/*
* THIS FILE IS FOR TCP TEST
*/

/*
struct sockaddr_in {
        short   sin_family;
        u_short sin_port;
        struct  in_addr sin_addr;
        char    sin_zero[8];
};
*/

#include "sysInclude.h"

extern void tcp_DiscardPkt(char *pBuffer, int type);

extern void tcp_sendReport(int type);

extern void tcp_sendIpPkt(unsigned char *pData, UINT16 len, unsigned int  srcAddr, unsigned int dstAddr, UINT8	ttl);

extern int waitIpPacket(char *pBuffer, int timeout);

extern unsigned int getIpv4Address();

extern unsigned int getServerIpv4Address();

enum STATE {CLOSED, SYNSENT, ESTABLISHED, FINWAIT1, FINWAIT2, TIMEWAIT};

int gSrcPort = 2006;
int gDstNum = 2007;
int gSeqNum = 1;
int gAckNum = 0;
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



TCB *TCBlink = NULL;
int sockfd = 0;
unsigned int timeout = 5;
int buffersize = 65535;

unsigned short flag2num(char flag)
{
    unsigned short num = 0;
    switch (flag)
    {
    case PACKET_TYPE_DATA:
        num = 0;
        break;
    case PACKET_TYPE_SYN:
        num = 0x1 << 1;
        break;
    case PACKET_TYPE_SYN_ACK:
        num = (0x1 << 4) + (0x1 << 1);
        break;
    case PACKET_TYPE_ACK:
        num = 0x1 << 4;
        break;
    case PACKET_TYPE_FIN:
        num = 0x1;
    case PACKET_TYPE_FIN_ACK:
        num = (0x1 << 4) + (0x1);
        break;
    
    default:
        break;
    }
    return num;
}
char num2flag(unsigned short num)
{
    char flag;
    switch (num)
    {
    case 0:
        flag = PACKET_TYPE_DATA;
        break;
    case 0x1 << 1:
        flag = PACKET_TYPE_SYN;
        break;
    case (0x1 << 4) + (0x1 << 1):
        flag = PACKET_TYPE_SYN_ACK;
        break;
    case 0x1 << 4:
        flag = PACKET_TYPE_ACK;
        break;
    case 0x1:
        flag = PACKET_TYPE_FIN;
    case (0x1 << 4) + (0x1):
        flag = PACKET_TYPE_FIN_ACK;
        break;
    
    default:
        break;
    }
    return flag;
}
unsigned int getChecksum(unsigned int* pBuffer)
{
    unsigned int checksum = 0;
    for(int i = 0; i < 8; i++)
    {
        checksum += (pBuffer[i] >> 16) + (pBuffer[i] & 0xffff);
    }
    return ~((checksum >> 16) + (checksum & 0xffff));
}
TCB* getTCB(unsigned int dstAddr, unsigned short dstPost)
{
    TCB* nowtcb = TCBlink;
    while (nowtcb != NULL && (nowtcb->dstAddr != dstAddr || nowtcb->dstPort != dstPost))
    {
        nowtcb = nowtcb->next;
    }
    return nowtcb;
}
void setSeqAck(TCB* tcb, char* buffer)
{
    tcb->seq = ntohl(*(unsigned int*)(buffer+8));
    tcb->ack = ntohl(*(unsigned int*)(buffer+4)) + 1;
}
TCB* findTCB(int sockfd)
{
    TCB* nowtcb = TCBlink;
    while (nowtcb!=NULL && nowtcb->sockfd!=sockfd)
    {
        nowtcb = nowtcb->next;
    }
    return nowtcb;
}
int stud_tcp_input(char *pBuffer, unsigned short len, unsigned int srcAddr, unsigned int dstAddr)
{
    unsigned int myBuffer[8] = {0};
    myBuffer[0] = ntohl(srcAddr);
    myBuffer[1] = ntohl(dstAddr);
    myBuffer[2] = (6 << 16) + (len);
    for(int i = 3; i < 8; i++)
    {
        myBuffer[i] = ntohl(((unsigned int*)pBuffer)[i-3]);
    }
    unsigned short srcPort = (myBuffer[3]>>16) & 0xffff;
    unsigned short dstPort = myBuffer[3] & 0xffff;
    unsigned int seqnum = myBuffer[4];
    unsigned int acknum = myBuffer[5];
    unsigned short flag = (char)((myBuffer[6] >> 16) & 0xff);
    if (getChecksum(myBuffer) != 0 || myBuffer[0] != getIpv4Address())
    {
        return -1;
    }
    gAckNum += 1;
    TCB* tcb = getTCB(myBuffer[0], srcPort);
    if(tcb == NULL)
    {
        return -1;
    }
    if(acknum != tcb->seq + 1)
    {
        tcp_DiscardPkt(pBuffer, STUD_TCP_TEST_SEQNO_ERROR);
        return -1;
    }
    if(tcb->state == SYNSENT && num2flag(flag) == PACKET_TYPE_SYN_ACK)
    {
        tcb->seq = acknum;
        tcb->ack = seqnum + 1;
        stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, tcb->srcPort, tcb->dstPort, tcb->srcAddr, tcb->dstAddr);
        tcb->state = ESTABLISHED;
    }
    else if(tcb->state == FINWAIT1 && num2flag(flag) == PACKET_TYPE_ACK)
    {
        tcb->state = FINWAIT2;
    }
    else if(tcb->state == FINWAIT2 && num2flag(flag) == PACKET_TYPE_FIN)
    {
        tcb->seq = acknum;
        tcb->ack = seqnum + 1;
        tcb->state = TIMEWAIT;
        stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, tcb->srcPort, tcb->dstPort, tcb->srcAddr, tcb->dstAddr);
        tcb->state = CLOSED;
    }
    else
    {
        return -1;
    }
	return 0;
}

void stud_tcp_output(char *pData, unsigned short len, unsigned char flag, unsigned short srcPort, unsigned short dstPort, unsigned int srcAddr, unsigned int dstAddr)
{
    TCB *tcb = getTCB(dstAddr, dstPort);
    if(TCBlink == NULL)
    {
        tcb = new TCB(sockfd++);
        TCBlink = tcb;
        tcb->dstAddr = dstAddr;
        tcb->dstPort = dstPort;
        tcb->srcAddr = srcAddr;
        tcb->srcPort = srcPort;
        tcb->state = CLOSED;
        tcb->ack = 0;
        tcb->seq = 0;
    }
    
    if(tcb == NULL)
    {
        return;
    }

    unsigned int myBuffer[8] = {0};
    myBuffer[0] = ntohl(srcAddr);
    myBuffer[1] = ntohl(dstAddr);
    myBuffer[2] = (6 << 16) + (5+len/4);
    myBuffer[3] = ((unsigned int)srcPort << 16) + ((unsigned int)dstPort);
    myBuffer[4] = tcb->seq;
    myBuffer[5] = tcb->ack;
    myBuffer[6] = (20 << 26) + ((unsigned int)flag2num(flag) << 16);
    if(flag == PACKET_TYPE_SYN)
    {
        tcb->state = SYN_SENT;
    }
    else if(flag == PACKET_TYPE_FIN_ACK)
    {
        tcb->state = FINWAIT1;
    }
    unsigned int checksum = getChecksum(myBuffer);
    myBuffer[7] = (checksum << 16);
    for(int i = 3; i < 8; i++)
    {
        myBuffer[i] = htonl(myBuffer[i]);
    }
    unsigned short ttl = 5;
    tcp_sendIpPkt((unsigned char*)(myBuffer+3), len+20, srcAddr, dstAddr, ttl);
    return;
}

int stud_tcp_socket(int domain, int type, int protocol)
{
    TCB* tcb = new TCB(sockfd);
    sockfd += 1;
    tcb->next = TCBlink;
    TCBlink = tcb;
	return TCBlink->sockfd;
}

int stud_tcp_connect(int sockfd, struct sockaddr_in *addr, int addrlen)
{
    TCB* nowtcb = findTCB(sockfd);
    if(nowtcb == NULL)
    {
        return -1;
    }
    nowtcb->srcAddr = getIpv4Address();
    nowtcb->srcPort = gSrcPort;
    nowtcb->dstAddr = ntohl(addr->sin_addr.s_addr);
    nowtcb->dstPort = ntohl(addr->sin_port);
    stud_tcp_output(NULL, 0, PACKET_TYPE_SYN, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
    char buffer[buffersize];
    if (waitIpPacket(buffer, timeout) == -1)
        return -1;
    setSeqAck(nowtcb, buffer);
    stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
    nowtcb->state = ESTABLISHED;
    return 0;
}
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
    stud_tcp_output(NULL, 0, PACKET_TYPE_ACK, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
	return 0;
}

int stud_tcp_close(int sockfd)
{
    TCB *pretcb = NULL;
    TCB *nowtcb = TCBlink;
    while (nowtcb != NULL && tcb->sockfd != sockfd)
    {
        pretcb = nowtcb;
        nowtcb = nowtcb->next;
    }
    if(nowtcb == NULL)
        return -1;
    pretcb->next = nowtcb->next;
    if(nowtcb->state != ESTABLISHED)
    {
        delete nowtcb;
        return -1;
    }
    else
    {
        stud_tcp_output(NULL, 0, PACKET_TYPE_FIN_ACK, nowtcb->srcPort, nowtcb->dstPort, nowtcb->srcAddr, nowtcb->dstAddr);
        char buffer[buffersize];
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
    
    delete nowtcb;
	return 0;
}
