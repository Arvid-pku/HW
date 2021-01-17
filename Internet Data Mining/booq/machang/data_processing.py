import nltk
from nltk import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from collections import Counter
import re
import tqdm
import jsonlines

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()
sw = stopwords.words("english")
def clean_text(text):
    text = re.sub("[^a-zA-Z]", " ", text.lower())
    text_list = word_tokenize(text) #分词
    texts = []
    for word in text_list:
        word = word.replace("<br /><br />","")
        word = re.sub("[^a-zA-Z]"," ",word.lower())
        texts.append(" ".join(word.split()))
    text_list = texts
    #text_list = [lemmatizer.lemmatize(word) for word in text_list]
    text_list = [word for word in text_list if word not in sw]
    text_list = [word for word in text_list if len(word)>0 and ' ' not in word]
    return '    '.join(text_list)

def load_and_store(path,path_store,label_store):
    cnt = 0
    text_q = []
    text_p = []
    label =[]
    print('processing '+path)
    with open(path, "r+", encoding="utf8") as f:
        for item in jsonlines.Reader(f):
            answer = item['answer']
            if answer == True:
                label.append(1)
            else:
                label.append(0)
            question = str(item['question'])
            passage = str(item['passage'])
            text_q.append(clean_text(question))
            text_p.append(clean_text(passage))
    print('saving '+path_store)
    with open("passage_"+path_store,'w',encoding='utf-8') as f:
        for line in text_p:
            f.write(str(line)+'\n')
    with open("question_"+path_store,'w',encoding='utf-8') as f:
        for line in text_q:
            f.write(str(line)+'\n')
    with open(label_store,'w',encoding='utf-8') as f:
        for line in label:
            f.write(str(line)+'\n')

load_and_store('dev.jsonl','dev.txt','dev_label.txt')
