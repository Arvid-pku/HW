/*
* THIS FILE IS FOR IP FORWARD TEST
*/
#include "sysInclude.h"

// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address( );

// implemented by students
#include <iostream>
#include <bitset>
#include <iomanip>

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

unsigned int foundDest(unsigned int dest)
{
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

    if(myBuffer[4] == getIpv4Address() || (myBuffer[4] == (getIpv4Address() | 0xffffff)))
        fwd_LocalRcv(pBuffer, length);
    else
    {
        unsigned int next = foundDest(myBuffer[4]);
        if(next==STUD_FORWARD_TEST_NOROUTE)
        {
            fwd_DiscardPkt(pBuffer, next);
            return 1;
        }
        else
        {
            unsigned int ttl = myBuffer[2] >> 24;
            if(ttl <= 0)
            {
                fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
                return 1;
            }
            else
            {
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

