import os
import pickle
import paddlenlp

# 加载tokeniezer
from conf import MODELNAME

tokenizer = paddlenlp.transformers.GPTChineseTokenizer.from_pretrained(MODELNAME)

trainData = []
# 处理所有的公众号文章
for index, path in enumerate(os.listdir('banfoText')):
    if not path.endswith('.txt'):
        continue
    print(index, path)
    with open(os.path.join('banfoText', path), 'r+', encoding='utf-8') as f:
        data = f.read()
    data = tokenizer(text=data, return_token_type_ids=False)
    data = data['input_ids']
    start = -30
    lenght = 100
    step = 30
    if len(data) <= 2 * lenght:
        continue
    # 滑动窗口截断获取inputData和label
    while start + step + 1 < len(data) and start + step + lenght + 1 < len(data):
        start = start + step
        input_data = data[start: start + lenght]
        label = data[start + 1: start + lenght + 1]
        trainData.append([input_data, label])
    trainData.append([data[-lenght-1: -1], data[-lenght:]])

if not os.path.exists('preprocessData'):
    os.mkdir('preprocessData')
with open(os.path.join('preprocessData', 'trainData.pkl'), 'wb') as f:
    pickle.dump(trainData, f)

print(len(trainData))
print('done!')
