import torch
output=torch.FloatTensor([[0.5,0.6],[0.1,0.05]])
label = torch.FloatTensor([[0,1],[1,0]])
pred = torch.max(output, 1)[1]
truth = torch.max(label,1)[1]
print(pred)