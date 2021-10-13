# 半佛视频风格生成器

## 项目背景
半佛在2020年凭借众多沙雕表情包视频 + 魔性的文案迅速出圈。魔性的文案不能直接复制，但是沙雕表情包的视频可以直接生成。不妨做一个视频生成器，快快速生成此类视频风格的视频。简直自媒体的福音，抖音的狂欢。

### 思路：
1. 输入断句后的文案
2. 将文案根据短句分割，每句作为一条字幕
3. 根据字幕搜索表情包并选择设置
4. 利用语音合成手段合成配音
5. 重复3、4步骤，直到所有的字幕均完成表情包设定、字幕设定、配音设定
6. 合成视频并加入背景音乐
7. 导出成品

## 安装
1. 安装python3.8.3
2. 安装requirements.txt依赖
3. 运行`python main.py`

## TODO
- [ ] 优化gif显示
- [ ] 表情包尺寸的统一问题
- [x] 编辑保存防止异常退出工作丢失
- [ ] 支持修改文案
- [x] 文件名自定义
- [x] 使用的图片与未使用的图片缓存分开，依据文件名归档
- [x] 使用过的配音缓存分类归档

## Reference
[一键生成半佛仙人视频，表情包之王你也可以！](https://www.bilibili.com/video/BV1oz411e7Jk)

[MoviePy](https://zulko.github.io/moviepy/)

[斗图啦](https://www.doutula.com/article/list/)

[百度图片](https://image.baidu.com/)

[百度在线语音合成](https://cloud.baidu.com/product/speech/tts_online)
## License
[GNU General Public License v3.0](LICENSE)