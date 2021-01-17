import torch
import torch.nn.functional as F
from nltk.tokenize import word_tokenize
from .loaddata import load_data, write_data

# predict ： write and evaluate
def predict(filepath, model, wd2idx):
    model = model.to('cpu')
    goldlabel, texts = load_data(filepath=filepath)
    goldlabel = torch.tensor(goldlabel)
    labelis = []
    for text in texts:
        tokens = word_tokenize(text.lower())
        # padded_tokens = tokens + ['<pad>']*(max_len - len(tokens))
        text_len = [len(tokens)]
        input_id = [wd2idx.get(token, wd2idx['<unk>']) for token in tokens]
        input_id = torch.tensor(input_id).unsqueeze(dim=0)
        logits = model.forward(input_id, text_len)
        probs = F.softmax(logits, dim=1).squeeze(dim=0)
        labelis.append(int(torch.argmax(probs)))
    print(sum(goldlabel == torch.tensor(labelis))/len(goldlabel))
    write_data(filepath+'re', filepath, labelis=labelis)