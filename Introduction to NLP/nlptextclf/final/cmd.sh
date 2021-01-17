CUDA_VISIBLE_DEVICES=0 python main.py -mode train -model lstm -pretrainembed True -attention True -lr 0.0001 -hiddendim 128 -numlayers 2 -dropout 0.5 \
        -num_classes 4 -epochs 100 -batch_size 128 -earlystop 15 \
        -savedir lstmcheckpoint -traindataset data/train.csv -validdataset data/dev.csv -testdataset data/test.csv

CUDA_VISIBLE_DEVICES=0 python main.py -mode train -model lstm -pretrainembed True -attention True -lr 0.0005 -hiddendim 128 -numlayers 3 -dropout 0.5 \
        -num_classes 4 -epochs 100 -batch_size 128 -earlystop 10 \
        -savedir lstmcheckpoint -traindataset data/train.csv -validdataset data/dev.csv -testdataset data/test.csv


CUDA_VISIBLE_DEVICES=0 python main.py -mode train -model cnn -pretrainembed True -attention True -lr 0.001 -filter_size 3 4 5 6  -filter_num 200 200 200 100 -dropout 0.4 \
        -num_classes 4 -epochs 100 -batch_size 128 -earlystop 15 \
        -savedir cnncheckpoint -traindataset data/train.csv -validdataset data/dev.csv -testdataset data/test.csv



CUDA_VISIBLE_DEVICES=0 python main.py -mode predict -model lstm -checkpoint lstmcheckpoint/m-64.26491141319275-92.2716.pth.tar -pretrainembed True -attention True -lr 0.0001 -hiddendim 128 -numlayers 2 -dropout 0.5 \
        -num_classes 4 -epochs 100 -batch_size 128 -earlystop 15 \
        -savedir lstmcheckpoint -traindataset data/train.csv -validdataset data/dev.csv -testdataset data/test.csv
