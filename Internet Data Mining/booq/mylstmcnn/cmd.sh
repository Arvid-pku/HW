CUDA_VISIBLE_DEVICES=0 python main.py -mode train -model lstm -pretrainembed True -attention True -lr 0.0001 -hiddendim 128 -numlayers 2 -dropout 0.5 \
        -num_classes 2 -epochs 100 -batch_size 128 -earlystop 15 \
        -savedir lstmcheckpoint -traindataset data/train.jsonl -validdataset data/dev.jsonl -testdataset data/test.jsonl
