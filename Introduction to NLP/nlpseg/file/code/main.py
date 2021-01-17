import argparse
from tqdm import tqdm
from SPWS import StructuredPerceptronWordSeg
from utils import xy2outp, inp2xy


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--feature', type=int, default=8, choices=[5, 7, 8, 10], help='feature num')
    parser.add_argument('-t', '--train', type=str, help='train set path')
    parser.add_argument('-p', '--predict', type=str, help='test set path')
    parser.add_argument('-a', '--answer', type=str, default='answer.txt', help='output answer path')
    parser.add_argument('-s', '--save', type=str, help='save model path')
    parser.add_argument('-l', '--load', type=str, help='load model path')
    parser.add_argument('-i', '--iteration', type=int, default=8, help='iteration times')
    args = parser.parse_args()

    model = StructuredPerceptronWordSeg(loadpath=args.load, featureNum=args.feature)

    if args.train:
        for it in range(args.iteration):
            print(f'epoch {it+1} of {args.iteration}')
            with open(args.train, 'r', encoding='utf-8') as f:
                for line in tqdm(f, total=7e4):
                    if line.strip():
                        x, y = inp2xy(line.strip())
                        model.train(x, y)

    if args.save:
        model.save(args.save)
    
    if args.predict:
        ansf = open(args.answer, 'w', encoding='utf-8')
        with open(args.predict, 'r', encoding='utf-8') as testf:
            for line in tqdm(testf, total=16924):
                x, _ = inp2xy(line)
                y = model.predict(x)
                ansf.write(xy2outp(x, y)+'\n')
        ansf.close()

