import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F

class CNN_TCLF(nn.Module):
    def __init__(self
                ,pretrained_embedding=None
                ,freeze_embedding=False
                ,vocab_size=None
                ,embed_dim=300
                ,filter_sizes=[3, 4, 5]
                ,num_filters=[100, 100, 100]
                ,num_classes=4
                ,dropout=0.5):
        super(CNN_TCLF, self).__init__()
        if pretrained_embedding is not None:
            self.vocab_size, self.embed_dim = pretrained_embedding.shape
            self.embedding = nn.Embedding.from_pretrained(pretrained_embedding, freeze=freeze_embedding)
        else:
            self.embed_dim = embed_dim
            self.embedding = nn.Embedding(num_embeddings=vocab_size, 
                                            embedding_dim=self.embed_dim, 
                                            padding_idx=0, 
                                            max_norm=5.0)
        self.conv1d_list = nn.ModuleList([nn.Conv1d(in_channels=self.embed_dim, out_channels=num_filters[i], kernel_size=filter_sizes[i]) for i in range(len(filter_sizes))])
        self.fc = nn.Linear(np.sum(num_filters), num_classes)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, input_ids, input_len=None):
        x_embed = self.embedding(input_ids).float()
        x_reshaped = x_embed.permute(0, 2, 1)
        x_conv_list = [F.relu(conv1d(x_reshaped)) for conv1d in self.conv1d_list]
        x_pool_list = [F.max_pool1d(x_conv, kernel_size=x_conv.shape[2]) for x_conv in x_conv_list]
        x_fc = torch.cat([x_pool.squeeze(dim=2) for x_pool in x_pool_list], dim=1)
        logits = self.fc(self.dropout(x_fc))
        return logits

