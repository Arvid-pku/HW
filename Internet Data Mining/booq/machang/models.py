import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import numpy as np
class LSTM_variable_input(torch.nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim,glove_weights):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dropout = nn.Dropout(0.3)
        self.embeddings = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.embeddings.weight.data.copy_(torch.from_numpy(glove_weights))
        self.embeddings.weight.requires_grad = False  ## freeze embeddings
        self.lstm = nn.LSTM(embedding_dim, hidden_dim,num_layers=2, batch_first=True,bidirectional =True)
        self.norm = nn.BatchNorm1d(hidden_dim)
        self.linear = nn.Linear(hidden_dim, 2)

    def forward(self, x, s):
        x = self.embeddings(x)
        x = self.dropout(x)
        x_pack = pack_padded_sequence(x, s, batch_first=True, enforce_sorted=False)
        out_pack, (ht, ct) = self.lstm(x_pack)
        out = torch.relu(self.linear(self.norm(ht[-1])))
        return out

class Siamese_LSTM_variable_input(torch.nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim,glove_weights):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dropout = nn.Dropout(0.5)
        self.embeddings = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.embeddings.weight.data.copy_(torch.from_numpy(glove_weights))
        self.embeddings.weight.requires_grad = False  ## freeze embeddings
        self.lstm = nn.LSTM(embedding_dim, hidden_dim,num_layers=1, batch_first=True,bidirectional =True)
        self.lstm2 = nn.LSTM(embedding_dim, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        self.norm = nn.BatchNorm1d(2*hidden_dim)
        self.linear = nn.Linear(2*hidden_dim, 2)

    def forward(self, q,p, sq,sp):
        q = self.embeddings(q)
        p = self.embeddings(p)
        p = self.dropout(p)
        q_pack = pack_padded_sequence(q, sq, batch_first=True, enforce_sorted=False)
        out_pack_q, (ht_q, ct_q) = self.lstm(q_pack)
        p_pack = pack_padded_sequence(p, sp, batch_first=True, enforce_sorted=False)
        out_pack_p, (ht_p, ct_p) = self.lstm2(p_pack)
        out = torch.relu(self.linear(self.norm(torch.cat((ht_p[-1],ht_q[-1]),1))))
        return out

class RCNN_variable_input(torch.nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim,glove_weights):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dropout = nn.Dropout(0.3)
        self.embeddings = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.embeddings.weight.data.copy_(torch.from_numpy(glove_weights))
        self.embeddings.weight.requires_grad = False  ## freeze embeddings
        self.maxpool = nn.MaxPool1d(128)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim,num_layers=1, batch_first=True,bidirectional =True)
        self.linear = nn.Linear(hidden_dim*2+embedding_dim, 2)

    def forward(self, x, s):
        x = self.embeddings(x)
        x = self.dropout(x)
        #x_pack = pack_padded_sequence(x, s, batch_first=True, enforce_sorted=False)
        out,_ = self.lstm(x)
        out = torch.cat((x, out), 2)
        out = torch.relu(out)
        out = out.permute(0, 2,1)
        out = self.maxpool(out).squeeze()
        #print(out.size())
        out = self.linear(out)
        return out

class RCNN_variable_input(torch.nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim,glove_weights):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dropout = nn.Dropout(0.3)
        self.embeddings = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.embeddings.weight.data.copy_(torch.from_numpy(glove_weights))
        self.embeddings.weight.requires_grad = False  ## freeze embeddings
        self.maxpool = nn.MaxPool1d(128)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim,num_layers=1, batch_first=True,bidirectional =True)
        self.linear = nn.Linear(hidden_dim*2+embedding_dim, 2)

    def forward(self, x, s):
        x = self.embeddings(x)
        x = self.dropout(x)
        out, _ = self.lstm(x)
        out = torch.cat((x, out), 2)
        out = out.permute(0, 2, 1)
        out = self.maxpool(out).squeeze()
        out = self.linear(out)
        return out
class Fasttext(torch.nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, glove_weights):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dropout = nn.Dropout(0.3)
        self.embeddings = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.embeddings.weight.data.copy_(torch.from_numpy(glove_weights))
        self.embeddings.weight.requires_grad = True  ## freeze embeddings
        self.embedding_ngram2 = nn.Embedding(vocab_size, embedding_dim)
        self.embedding_ngram2.weight.data.copy_(torch.from_numpy(glove_weights))
        self.embedding_ngram3 = nn.Embedding(vocab_size, embedding_dim)
        #self.embedding_ngram3.weight.data.copy_(torch.from_numpy(glove_weights))
        self.fc1 = nn.Linear(embedding_dim * 3, hidden_dim)
        # self.dropout2 = nn.Dropout(config.dropout)
        self.norm = nn.BatchNorm1d(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 2)

    def forward(self, x, s):
        out_word = self.embeddings(x)
        out_bigram = self.embedding_ngram2(x)
        out_trigram = self.embedding_ngram3(x)
        out = torch.cat((out_word, out_bigram, out_trigram), -1)
        out = out.mean(dim=1)
        out = self.dropout(out)
        out = self.fc1(out)
        out = torch.relu(out)
        out = self.norm(out)
        out = self.fc2(out)
        return out