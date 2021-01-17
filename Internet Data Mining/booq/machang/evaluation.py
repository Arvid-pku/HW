import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from models import LSTM_variable_input,RCNN_variable_input,Fasttext
import seaborn as sns
import torch.optim as optim
def evaluate(model, test_loader, version='title', threshold=0.5):
    y_pred = []
    y_true = []
    model.eval()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    with torch.no_grad():
        for (text,label,textlen) in test_loader:
            text = text.long().to(device)
            label = label.float().to(device)
            textlen = textlen.to(device)
            output = model(text, textlen)
            pred = torch.max(output, 1)[1]
            truth = torch.max(label, 1)[1]
            y_pred.extend(pred.tolist())
            y_true.extend(truth.tolist())

    target_names = ['human', 'machine']
    print(classification_report(y_true, y_pred, target_names=target_names))
    print("-----start storing result-----")
    with open('test_result.txt','w',encoding='utf-8') as f:
        for line in y_pred:
            f.write(str(line)+'\n')

def load_checkpoint(load_path, model, optimizer):
    if load_path == None:
        return
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    state_dict = torch.load(load_path, map_location=device)
    print(f'Model loaded from <== {load_path}')

    model.load_state_dict(state_dict['model_state_dict'])
    optimizer.load_state_dict(state_dict['optimizer_state_dict'])

    return state_dict['valid_loss']

def evaluate_new(model, test_loader, version='title', threshold=0.5):
    y_pred = []
    y_true = []
    model.eval()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    for (text, label) in test_loader:
        text = text.to(device)
        label = label.float().to(device)
        output = model(text)
        pred = torch.max(output, 1)[1]
        truth = torch.max(label, 1)[1]
        y_pred.extend(pred.tolist())
        y_true.extend(truth.tolist())

    target_names = ['human', 'machine']
    print(classification_report(y_true, y_pred, target_names=target_names))
    print("-----start storing result-----")
    with open('test_result.txt','w',encoding='utf-8') as f:
        for line in y_pred:
            f.write(str(line)+'\n')

def load_checkpoint(load_path, model, optimizer):
    if load_path == None:
        return
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    state_dict = torch.load(load_path, map_location=device)
    print(f'Model loaded from <== {load_path}')

    model.load_state_dict(state_dict['model_state_dict'])
    optimizer.load_state_dict(state_dict['optimizer_state_dict'])

    return state_dict['valid_loss']

