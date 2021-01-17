from struct import pack
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

class LSTM_TCLF(nn.Module):
    def __init__(self
                ,pretrained_embedding=None
                ,freeze_embedding=False
                ,vocab_size=None
                ,hidden_size=200
                ,bidirectional=True
                ,attention=True
                ,embed_dim=300
                ,num_classes=4
                ,num_layers = 2
                ,dropout=0.5):

        super(LSTM_TCLF, self).__init__()
        if pretrained_embedding is not None:
            self.vocab_size, self.embed_dim = pretrained_embedding.shape
            self.embedding = nn.Embedding.from_pretrained(pretrained_embedding, freeze=freeze_embedding)
        else:
            self.embed_dim = embed_dim
            self.embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=self.embed_dim, padding_idx=0, max_norm=5.0)

        self.hidden_size = hidden_size
        self.attention = attention
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size=self.embed_dim,
                            hidden_size=hidden_size,
                            num_layers=num_layers,
                            batch_first=True,
                            dropout=dropout,
                            bidirectional=bidirectional)

        self.fc = nn.Linear(2*hidden_size, num_classes)
        self.dropout = nn.Dropout(dropout)
        self.wp = nn.Parameter(torch.Tensor(hidden_size*2, hidden_size*2))
        self.up = nn.Parameter(torch.Tensor(hidden_size*2, 1))
        nn.init.uniform_(self.wp, -0.1, 0.1)
        nn.init.uniform_(self.up, -0.1, 0.1)

    def attention_net(self, output):
        u = torch.tanh(torch.matmul(output, self.wp))
        att = torch.matmul(u, self.up)
        att_score = F.softmax(att, dim=1)
        scored_output = output * att_score
        context = torch.sum(scored_output, dim=1)
        return context
        
    def forward(self, text, text_len):

        text_emb = self.dropout(self.embedding(text))

        packed_input = pack_padded_sequence(text_emb, text_len, batch_first=True, enforce_sorted=False)
        packed_output, (final_hidden_state, final_cell_state) = self.lstm(packed_input.float())
        output, text_len = pad_packed_sequence(packed_output, batch_first=True)
        if self.attention:
            output = self.attention_net(output)
        else:
            output = final_hidden_state[-1]
        logits = self.fc(output)
        return logits