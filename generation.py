import paddle
import paddlenlp

from conf import MODELNAME

paddle.set_device('gpu')
gptModel = paddlenlp.transformers.GPTModel.from_pretrained('models')
gptModel = paddlenlp.transformers.GPTForPretraining(gptModel)
gptModel.eval()
tokenizer = paddlenlp.transformers.GPTChineseTokenizer.from_pretrained(MODELNAME)


def getPredictText(text: str, length: int = 200) -> str:
    """
    生成半佛风格文本
    :param text: 前面部分的文本
    :param length: 生成文本长度
    :return: 生成的文本
    """
    encodedText = tokenizer(text=text, return_token_type_ids=False)
    inputIds = paddle.to_tensor(encodedText['input_ids'], dtype='int64').unsqueeze(0)
    ids, _ = gptModel.generate(input_ids=inputIds, max_length=length, min_length=32, decode_strategy='sampling')
    ids = ids[0].numpy().tolist()
    # 使用tokenizer将生成的id转为文本
    generatedText = tokenizer.convert_ids_to_string(ids)
    return generatedText
