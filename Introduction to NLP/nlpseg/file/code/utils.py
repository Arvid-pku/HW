def inp2xy(inp):
    wordlist = inp.split()
    y = []
    for word in wordlist:
        if (len(word)) == 1:
            y.append(3)
        else:
            y.extend([0]+[1]*(len(word) - 2)+[2])
    x = ''.join(wordlist)
    return x, y

def xy2outp(x, y):
    outp = ''
    tmp = ''
    for chr, lb in zip(x, y):
        if lb == 0 or lb == 1:
            tmp += chr
        else:
            outp += tmp + chr + ' '
            tmp = ''
    return outp