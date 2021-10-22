import os
import pickle

import paddle
import paddlenlp
from paddle.io import Dataset, DataLoader
import paddle.nn as nn

from conf import MODELNAME


class BanfoDataset(Dataset):
    def __init__(self, data, tokenizer):
        super().__init__()
        self.data = data
        self.tokenizer = tokenizer

    def __getitem__(self, idx):
        return paddle.to_tensor(self.data[idx][0], dtype='int64'), paddle.to_tensor(self.data[idx][1], dtype='int64')

    def __len__(self):
        return len(self.data)


paddle.set_device('gpu')

gptModel = paddlenlp.transformers.GPTModel.from_pretrained(MODELNAME)
gptModel = paddlenlp.transformers.GPTForPretraining(gptModel)
tokenizer = paddlenlp.transformers.GPTChineseTokenizer.from_pretrained(MODELNAME)

# 有本地模型存在，则加载本地模型
checkpoint = os.path.join('models', 'model_state.pdparams')
if os.path.exists(checkpoint):
    model_state = paddle.load(checkpoint)
    gptModel.set_state_dict(model_state)

# 设置为评估模型
gptModel.eval()

# 测试效果
encodedText = tokenizer(text='前段时间我跟一个老大哥一起吃火锅。大哥的孩子，都上学了', return_token_type_ids=False)
ids, _ = gptModel.generate(input_ids=paddle.to_tensor(encodedText['input_ids'], dtype='int64').unsqueeze(0),
                           max_length=16, min_length=1, decode_strategy='sampling')
ids = ids[0].numpy().tolist()
# 使用tokenizer将生成的id转为文本
text = tokenizer.convert_ids_to_string(ids)
print('generation text is {}'.format(text))

# 加载训练数据
with open(os.path.join('preprocessData', 'trainData.pkl'), 'rb') as f:
    data = pickle.load(f)

trainDataLoader = DataLoader(dataset=BanfoDataset(data, tokenizer), batch_size=64, shuffle=True, return_list=True)

numEpochs = 100
learningRate = 2e-5
warmupProportion = 0.1
weightDecay = 0.1

maxSteps = (len(trainDataLoader) * numEpochs)
lr_scheduler = paddle.optimizer.lr.LambdaDecay(learningRate,
                                               lambda currentStep, numWarmupSteps=maxSteps * warmupProportion, numTrainingSteps=maxSteps: float(currentStep) / float(max(1, numWarmupSteps)) if currentStep < numWarmupSteps else max(0.0, float(numTrainingSteps - currentStep) / float(max(1, numTrainingSteps - numWarmupSteps))))

optimizer = paddle.optimizer.AdamW(learning_rate=lr_scheduler,
                                   parameters=gptModel.parameters(),
                                   weight_decay=weightDecay,
                                   grad_clip=nn.ClipGradByGlobalNorm(1.0),
                                   apply_decay_param_fun=lambda x: x in [
                                       p.name for n, p in gptModel.named_parameters()
                                       if not any(nd in n for nd in ["bias", "norm"])
                                   ])

globalStep = 1
save_steps = 100
criterion = paddle.nn.loss.CrossEntropyLoss()
gptModel.train()
for epoch in range(numEpochs):
    for step, batch in enumerate(trainDataLoader, start=1):
        ids, label = batch
        logits, _ = gptModel.forward(ids, use_cache=True)
        loss = criterion(logits, label)
        loss.backward()
        optimizer.step()
        lr_scheduler.step()
        optimizer.clear_gradients()
        if globalStep % save_steps == 0:
            print(globalStep, loss.numpy())
            gptModel.save_pretrained('models')
        globalStep += 1
