
from collections import Counter
import numpy as np
from torch.utils.data import Dataset, DataLoader
import torch
from models import LSTM_variable_input,RCNN_variable_input,Fasttext,Siamese_LSTM_variable_input
import torch.optim as optim
import torch.nn.functional as F
import matplotlib.pyplot as plt
from utils import train,siamese_train
from evaluation import evaluate,load_checkpoint
def read_data(path):
    lst_p = []
    with open("passage_"+path,'r',encoding='UTF-8') as p:
        for line in p.readlines():
            if line.rstrip('\n').isdigit():
                lst_p.append(int(line))
            else:
               lst_p.append(line.rstrip('\n').split('    '))
    lst_q = []
    with open("question_" + path, 'r', encoding='UTF-8') as p:
        for line in p.readlines():
            if line.rstrip('\n').isdigit():
                lst_q.append(int(line))
            else:
                lst_q.append(line.rstrip('\n').split('    '))
    lst =[]
    for i in range(len(lst_p)):
        lst.append([lst_q[i],lst_p[i]])
    return lst,lst_p,lst_q
def read_label(path):
    lst= []
    with open(path,'r',encoding='UTF-8') as p:
        for line in p.readlines():
            if line.rstrip('\n').isdigit():
                lst.append(int(line))
            else:
               lst.append(line.rstrip('\n').split('    '))
    return lst

train_set,train_passage,train_question =  read_data('train.txt')
train_label =  read_label('train_label.txt')
val_set,val_passage,val_question=  read_data('dev.txt')
val_label =  read_label('dev_label.txt')
text = train_passage+val_passage+train_question+val_question
counts = Counter()
for t in text:
    counts.update(t)
print("num_words before:",len(counts.keys()))
for word in list(counts):
    if counts[word] < 5:
        del counts[word]
print("num_words after:",len(counts.keys()))

#creating vocabulary
vocab2index = {"":0, "UNK":1}
words = ["", "UNK"]
for word in counts:
    vocab2index[word] = len(words)
    words.append(word)
vocab_size =len(vocab2index)
#print(vocab2index)

def encode_sentence(text, vocab2index, N=128):
    encoded = np.zeros(N, dtype=int)
    enc1 = np.array([vocab2index.get(word, vocab2index["UNK"]) for word in text])
    length = min(N, len(enc1))
    encoded[:length] = enc1[:length]
    return encoded,length
def encode_label(label):
    return np.array([1,0]) if label==1 else np.array([0,1])


train_tokens = [(encode_sentence(t[0],vocab2index),encode_sentence(t[1],vocab2index) )for t in train_set]
val_tokens = [(encode_sentence(t[0],vocab2index),encode_sentence(t[1],vocab2index) ) for t in val_set]
train_labels =[encode_label(l) for l in train_label]
val_labels =[encode_label(l) for l in val_label]

class TextDataset(Dataset):
    def __init__(self, X, Y):
        self.X = X
        self.y = Y
    def __len__(self):
        return len(self.y)
    def __getitem__(self, idx):
        return torch.from_numpy(self.X[idx][0][0].astype(np.int32)),torch.from_numpy(self.X[idx][1][0].astype(np.int32)), self.y[idx], self.X[idx][0][1],self.X[idx][1][1]
def load_glove_vectors(glove_file="glove.6B/glove.6B.300d.txt"):
    """Load the glove word vectors"""
    word_vectors = {}
    with open(glove_file,encoding='UTF-8') as f:
        for line in f:
            split = line.split()
            word_vectors[split[0]] = np.array([float(x) for x in split[1:]])
    return word_vectors

def get_emb_matrix(pretrained, word_counts, emb_size = 300):
    """ Creates embedding matrix from word vectors"""
    vocab_size = len(word_counts) + 2
    vocab_to_idx = {}
    vocab = ["", "UNK"]
    W = np.zeros((vocab_size, emb_size), dtype="float32")
    W[0] = np.zeros(emb_size, dtype='float32') # adding a vector for padding
    W[1] = np.random.uniform(-0.25, 0.25, emb_size) # adding a vector for unknown words
    vocab_to_idx["UNK"] = 1
    i = 2
    for word in word_counts:
        if word in word_vecs:
            W[i] = word_vecs[word]
        else:
            W[i] = np.random.uniform(-0.25,0.25, emb_size)
        vocab_to_idx[word] = i
        vocab.append(word)
        i += 1
    return W, np.array(vocab), vocab_to_idx
word_vecs = load_glove_vectors()
pretrained_weights, vocab, vocab2index = get_emb_matrix(word_vecs, counts)

device = "cuda:0" if torch.cuda.is_available() else "cpu"
batch_size = 256
epochs = 30
is_training = True
print("building dataset")
train_ds = TextDataset(train_tokens, train_labels)
valid_ds = TextDataset(val_tokens, val_labels)
#print(train_ds.__getitem__(0))
train_dataloader = DataLoader(train_ds, batch_size=batch_size,
                        shuffle=True)
val_dataloader = DataLoader(valid_ds, batch_size=batch_size,
                        shuffle=True)
if is_training:
    model =Siamese_LSTM_variable_input(vocab_size, 300, 128,pretrained_weights)
    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    print("starts training")
    acc,loss,val_acc,val_loss = siamese_train(model=model, optimizer=optimizer,train_loader=train_dataloader,valid_loader=val_dataloader,file_path='save2/lstm',eval_every=5, num_epochs=epochs)
    plt.plot(range(epochs),acc,label="train_accuracy")
    plt.plot(range(epochs),val_acc,label="validation_accuracy")
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.show()

    plt.plot(range(epochs),loss,label="train_loss")
    plt.plot(range(epochs),val_loss,label="validation_loss")
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
