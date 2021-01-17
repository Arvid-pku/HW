import json
class StructuredPerceptronWordSeg:
    def __init__(self, loadpath=None, featureNum=8):
        if loadpath:
            model = json.load(open(loadpath, encoding='utf-8'))
            self.featureNum = model['featureNum']
            self.transitionP = model['transitionP']
            self.emissionP = model['emissionP']
        else:
            self.featureNum = featureNum
            self.transitionP = [[0]*4 for i in range(4)]
            self.emissionP = [{} for i in range(4)]

    def save(self, savepath):
        json.dump({'featureNum': self.featureNum, 'transitionP': self.transitionP, 'emissionP': self.emissionP}, 
                    open(savepath, 'w', encoding='utf-8'),
                    indent=4)


    def getfeature(self, sentence):
        sentfeature = []
        for i in range(len(sentence)):
            l2 = sentence[i-2] if i-2 >= 0 else '*'
            l1 = sentence[i-1] if i-1 >= 0 else '*'
            m = sentence[i]
            r1 = sentence[i+1] if i+1 < len(sentence) else '*'
            r2 = sentence[i+2] if i+2 < len(sentence) else '*'
            if self.featureNum == 5:
                sentfeature.append([m+'1', l1+'2', r1+'3', l1+m+'4', m+r1+'5'])
            elif self.featureNum == 7:
                sentfeature.append([m+'1', l1+'2', r1+'3', l1+m+'4', m+r1+'5', l2+l1+'6', r1+r2+'7'])
            elif self.featureNum == 8:
                sentfeature.append([m+'1', l1+'2', r1+'3', l1+m+'4', m+r1+'5', l2+l1+'6', r1+r2+'7', 
                                l2+l1+m+'8'])
            elif self.featureNum == 10:
                sentfeature.append([m+'1', l1+'2', r1+'3', l1+m+'4', m+r1+'5', l2+l1+'6', r1+r2+'7', 
                                l2+l1+m+'8', l1+m+r1+'9', m+r1+r2+'0'])
        return sentfeature

    def updateP(self, sentence, label, how):
        # print(label)
        sentfeature = self.getfeature(sentence)
        for i in range(1, len(label)-1):
            self.transitionP[label[i-1]][label[i]] += how
        for tag, chrfeature in zip(label, sentfeature):
            for feature in chrfeature:
                try:
                    self.emissionP[tag][feature] += how
                except TypeError:
                    print(label)
                    print(chrfeature)
                    raise TypeError

    def train(self, sentence, label):
        label_p = self.predict(sentence)
        if label != label_p:
            self.updateP(sentence, label, 1)
            self.updateP(sentence, label_p, -1)

        

    def predict(self, sentence):
        def getchremissionP(tag, chrfeature):
            for feature in chrfeature:
                if not feature in self.emissionP[tag].keys():
                    for i in range(len(self.emissionP)):
                        self.emissionP[i][feature] = 0

            return sum([self.emissionP[tag][feature] for feature in chrfeature])

        def getallpossiblep(pre, to, chrfeature):
            # j=0
            # print(pre[j][0], self.transitionP[j][to], getchremissionP(to, chrfeature))
            return [[pre[j][0]+self.transitionP[j][to]+getchremissionP(to, chrfeature), j] for j in range(4)]

        sentfeature = self.getfeature(sentence)
        dp = [[[getchremissionP(i, sentfeature[0]), None] for i in range(4)]]
        
        for chrnum in range(1, len(sentence)):
            # print(dp)
            dp.append([max(getallpossiblep(dp[chrnum-1], i, sentfeature[chrnum])) for i in range(4)])
        
        label = []
        if len(sentence) > 1:
            label.append(max(dp[-1])[1])
            nowpos = len(sentence) - 1
            while nowpos > 1:
                nowpos -= 1
                label.append(dp[nowpos][label[-1]][1])
            
            label = list(reversed(label))
        label.append(dp[-1].index(max(dp[-1])))
        return label
