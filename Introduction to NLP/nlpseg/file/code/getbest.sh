python --feature 10 --train train.txt --predict dev.txt --answer answer.txt --save bestmodel.json --iteration 14
cd 评测脚本
perl score word.txt ../dev.txt ../answer.txt > score.txt