import random
import time
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# get length of every sentence
def getlen(b_input_ids):
    text_len = []
    for lis in b_input_ids:
        if 0 in lis:
            text_len.append(lis.cpu().numpy().tolist().index(0))
        else:
            text_len.append(len(lis))
    return text_len

# evaluate
def evaluate(model, val_dataloader, device):
    model.eval()
    val_acc = []
    val_loss = []
    loss_fn = nn.CrossEntropyLoss()
    for batch in tqdm(val_dataloader):
        b_input_ids, b_labels = tuple(t.to(device) for t in batch)
        text_len = getlen(b_input_ids)
        with torch.no_grad():
            logits = model(b_input_ids, text_len)
        loss = loss_fn(logits, b_labels)
        val_loss.append(loss.item())
        preds = torch.argmax(logits, dim=1).flatten()
        acc = (preds == b_labels).cpu().numpy().mean()*100
        val_acc.append(acc)
        
    # loss and acc
    val_loss = np.mean(val_loss)
    val_acc = np.mean(val_acc)
    return val_loss, val_acc