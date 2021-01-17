import pandas as pd
from sklearn.model_selection import train_test_split

def raw2csv(filepath, topath, istrain):
    tworows = {'text':[], 'label':[]}
    with open(filepath, 'r') as f:
        for line in f:
            tworows['text'].append(line[:-2].strip()[:maxlen])
            tworows['label'].append(line[-2])
    if istrain:
        train_texts, val_texts, train_labels, val_labels = train_test_split(tworows['text'], tworows['label'], test_size=.2)
        trainset = {'text':train_texts, 'label':train_labels}
        valset = {'text':val_texts, 'label':val_labels}
        data_df = pd.DataFrame(trainset)
        data_df.to_csv(topath+'train.csv', index=False)
        data_df = pd.DataFrame(valset)
        data_df.to_csv(topath+'val.csv', index=False)
    else:
        data_df = pd.DataFrame(tworows)
        data_df.to_csv(topath, index=False)

raw2csv('oridata/train.txt', 'data/', True)
raw2csv('oridata/test1.txt', 'data/test.csv', False)


with open('oridata/train.txt') as f:

    lines = []
    for line in f:
        lines.append(line[:-2].strip().replace("\t", " ") + '\t' + line[-2] + '\n')

    train, val = train_test_split(lines, test_size=.2)
    
    ftrain = open('Bert-TextClassification/mydata/train.tsv', 'w')
    ftrain.writelines(train)
    ftrain.close()
    
    fval = open('Bert-TextClassification/mydata/val.tsv', 'w')
    fval.writelines(val)
    fval.close()

with open('oridata/test2_no_lable.txt') as f:

    lines = []
    for line in f:
        lines.append(' '.join(line[:-2].strip().replace("\t", " ").replace("'", "").replace('"', "").split(' ')) + '\t' + line[-2] + '\n')

    ftrain = open('Bert-TextClassification/mydata/test.tsv', 'w')

    ftrain.write('text\tlabel\n')
    ftrain.writelines(lines)
    ftrain.close()