import random
import time
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.nn.functional as F
from .evaluate import evaluate

# get length
def getlen(b_input_ids):
    text_len = []
    for lis in b_input_ids:
        if 0 in lis:
            text_len.append(lis.cpu().numpy().tolist().index(0))
        else:
            text_len.append(len(lis))
    return text_len
    
# train
def train(model, optimizer, train_dataloader, val_dataloader=None, epochs=10, device=None, savedir=None, earlystop=10):
    best_acc = 0
    loss_fn = nn.CrossEntropyLoss()
    losslist = []
    acclist = []
    stop = 0
    nowepoch = 0

    # loop
    for epoch_i in range(epochs):
        nowepoch = epoch_i
        t_start = time.time()
        model.train()
        total_loss = 0
        
        # train
        for batch in tqdm(train_dataloader):
            b_input_ids, b_labels = tuple(t.to(device) for t in batch)
            model.zero_grad()
            text_len = getlen(b_input_ids)
            logits = model(b_input_ids, text_len)
            loss = loss_fn(logits, b_labels)
            total_loss += loss.item()
            losslist.append(loss.item())
            loss.backward()
            optimizer.step()
        avg_train_loss = total_loss / len(train_dataloader)

        # evaluate
        if val_dataloader is not None:
            val_loss, val_acc = evaluate(model, val_dataloader, device)
            acclist.append(val_acc)
            if val_acc > best_acc:
                stop = 0
                best_acc = val_acc
                time_elapsed = time.time() - t_start

                # save
                torch.save({'epoch': epoch_i + 1, 'state_dict': model.state_dict(), 'best_acc': best_acc, 'optimizer': optimizer.state_dict()},
                            savedir + '/m-' + str("%.4f" % best_acc) + '.pth.tar')
            else:
                stop += 1
            print(f'epoch: {epoch_i}/{epochs} | avg_train_loss: {avg_train_loss} | val_loss: {val_loss} | val_acc: {val_acc} | best_acc: {best_acc} | time: {time_elapsed}')
            if stop >= earlystop:
                break
    print('\n')
    print(f'Training complete. Best acc = {best_acc:.3f}%.')
    return losslist, acclist, nowepoch

