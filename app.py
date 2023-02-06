import json

import openai
from flask import Flask, request
from flask_caching import Cache
# import redis
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
env_dist = os.environ
cache = Cache(app, config={'CACHE_TYPE': 'simple', "CACHE_DEFAULT_TIMEOUT": 30})


# app.config['POOL'] = redis.ConnectionPool(host=env_dist.get("REDIS_HOST"), port=16443,
#                                           password=env_dist.get("REDIS_PASSWORD"))

def text_reply(ans):
    return json.dumps({
        "err_code": 0,
        "data_list": [
            {
                "ans": ans,
            }
        ]
    })


@app.route('/login', methods=['GET'])
def login():
    openid = request.args.get('openid')
    # 保证短时间内数据不变
    timestamp = int(int(datetime.now().timestamp()) / 600)
    token = '8FB3F46C-2DDB-471E-AA51-2DD40BE859D6'
    list = [token, str(timestamp), openid]
    # 对token、timestamp和nonce按字典排序
    list.sort()
    # 将排序后的结果拼接成一个字符串
    list = ''.join(list)
    # 对结果进行sha1加密
    hashcode = hashlib.sha1(list.encode('utf8')).hexdigest()

    # r = redis.Redis(connection_pool=app.config['POOL'])
    k = hashcode[:6]
    # r.hset(k, 'openid', openid)
    # r.expire(k, 600)
    return json.dumps({
        "err_code": 0,
        "data_list": [
            {
                "ans": k,
            }
        ]
    })


@app.route('/talk/chat_gpt', methods=['GET'])
def chat_gpt():
    prompt = request.args.get('query')
    prompt = prompt + "，需要精简概括"
    if cache.get(prompt + "had_calc"):
        if cache.get(prompt):
            return text_reply(cache.get(prompt))
        return text_reply("当前问题正在计算中，请5秒后原样再发一次。")
    else:
        return text_reply(generate_response(prompt))


@cache.memoize(timeout=60)
def generate_response(prompt):
    cache.set(prompt + "had_calc", "1", timeout=5)
    openai.api_key = os.getenv("api_key")
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    message = response.choices[0].text
    ans = message.strip()
    cache.set(prompt, ans, timeout=300)
    cache.delete(prompt + "had_calc")
    return ans


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
