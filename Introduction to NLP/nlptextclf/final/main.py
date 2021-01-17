import torch
import argparse
import torch.optim as optim
from func.train import train
from func.predict import predict
from func.evaluate import evaluate
from func.loaddata import get_dataloader, load_data
from model.lstm import LSTM_TCLF
from model.cnn import CNN_TCLF
import numpy as np
import matplotlib.pyplot as plt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # task
    parser.add_argument('-mode', type=str, default='train', choices=['train', 'predict'] ,help='choose mode')
    
    # model
    parser.add_argument('-model', type=str, default='lstm', choices=['cnn', 'lstm'] ,help='choose model to do text classification')
    parser.add_argument('-pretrainembed', type=bool, default=True, help='whether use pretrained word embedding')
    parser.add_argument('-freezembed', type=bool, default=False, help='whether finetune pretrained word embedding')
    parser.add_argument('-attention', type=bool, default=True, help='whether use attention in lstm')
    parser.add_argument('-bidct', type=bool, default=True, help='whether use bilstm or normal lstm')

    

    parser.add_argument('-lr', type=float, default=0.001, help='initial learning rate')
    parser.add_argument('-filter_size', nargs='+', type=int, default=[3, 4, 5], help='the size of cnn filter')
    parser.add_argument('-filter_num', nargs='+', type=int, default=[100, 100, 100], help='the num of every cnn filter')
    parser.add_argument('-hiddendim', type=int, default=64, help='the dimention of lstm hidden layer')
    parser.add_argument('-numlayers', type=int, default=2, help='the num of lstm layer')
    parser.add_argument('-dropout', type=float, default=0.3, help='drop out rate')
    parser.add_argument('-num_classes', type=int, default=4, help='the num of class labels')
    
    # train
    parser.add_argument('-epochs', type=int, default=64, help='number of epochs for train')
    parser.add_argument('-batch_size', type=int, default=64, help='batch size for training')
    parser.add_argument('-earlystop', type=int, default=5, help='stop if the acc not decrease')

    # path
    parser.add_argument('-checkpoint', type=str, default=None, help='the path to load model checkpoint')
    parser.add_argument('-savedir', type=str, default='lstmcheckpoint', help='the path to save model checkpoint')
    parser.add_argument('-traindataset', type=str, default='data/train.csv', help='the path of train data set')
    parser.add_argument('-validdataset', type=str, default='data/dev.csv', help='the path of valid data set')
    parser.add_argument('-testdataset', type=str, default='data/dev.csv', help='the path of test data set')
    args = parser.parse_args()

    # GPU
    if torch.cuda.is_available():       
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    # data staff
    wd2idx, embeddings, train_dataloader, val_dataloader = get_dataloader(args.traindataset, args.validdataset, args.testdataset, '../fastText/crawl-300d-2M.vec', args.batch_size)
    if args.pretrainembed == False:
        embeddings = None
    
    # model
    if args.model == 'cnn':
        model = CNN_TCLF(
            pretrained_embedding=embeddings, 
            freeze_embedding=args.freezembed,
            embed_dim=300,
            vocab_size=10000,
            filter_sizes=args.filter_size,
            num_filters=args.filter_num,
            num_classes=args.num_classes,
            dropout=args.dropout
        )
    else:
        model = LSTM_TCLF(
            pretrained_embedding=embeddings, 
            freeze_embedding=args.freezembed,
            embed_dim=300,
            vocab_size=10000,
            hidden_size=args.hiddendim,
            bidirectional=args.bidct,
            attention=args.attention,
            num_classes=args.num_classes,
            dropout=args.dropout
        )

    model.to(device)
    optimizer = optim.Adam(
        model.parameters(),
        lr=args.lr,
    )
    if args.checkpoint != None:
        model_CKPT = torch.load(args.checkpoint)
        model.load_state_dict(model_CKPT['state_dict'])
        optimizer.load_state_dict(model_CKPT['optimizer'])

    # train
    if args.mode == 'train':
        model.train()
        losslist, acclist, nowepoch = train(model, optimizer, train_dataloader, val_dataloader, epochs=args.epochs, device=device, savedir=args.savedir, earlystop=args.earlystop)
        plt.plot([i for i in range(len(losslist))], losslist, 'r')
        plt.xlabel('iterations')
        plt.ylabel('loss')
        plt.savefig(args.model+str(max(acclist))+'loss.jpg')
        
        plt.figure()

        plt.plot([i for i in range(len(acclist))], acclist, 'b')
        plt.xlabel('iterations')
        plt.ylabel('acc')
        plt.ylim((min(acclist)-1, max(acclist)+1))
        plt.savefig(args.model+str(max(acclist))+'acc.jpg')
        plt.show()
        f = open('res.txt', 'a')
        f.write(str(max(acclist)) + '\n')
        f.close()
        
    # predict
    else:
        model.eval()
        predict(args.testdataset, model, wd2idx)




# 写完不同模式下的配置， 写完命令行