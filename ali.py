def get_access_token():
    """
    文心一言
    使用 API Key，Secret Key 获取access_token，替换下列示例中的应用API Key、应用Secret Key
    """

    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=Y5GE8G3wdViXrvnZlwHxne6T&client_secret=6rJeWVROXCbypEs3vBGMucc1ehFstnl6"
    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("access_token")


def generate_response(content, parameter, api_url, model):
    if model == "wenxin":
        url = api_url
        json_data = json.dumps({
            'messages': content,
            'temperature': parameter["temperature"],
            'max_tokens': parameter["max_tokens"],
            'presence_penalty': parameter["presence_penalty"],
            "stream": True
        })
        headers = {
            'Content-Type': 'application/json',
            "Accept": "application/json"
        }

        # if parameter["max_tokens"] == 0:
        #     json_data.pop("max_tokens")

        response = requests.post(url, headers=headers, data=json_data, stream=True)
    elif model == "kimi":
        url = api_url
        headers = {
            'Authorization': "sk-yao31fgN3DLw0OoBAO51YMRPPE0eKqe3oO4A6lB5W4H3vmHP",
            'Content-Type': 'application/json',
        }

        json_data = {'model': "moonshot-v1-8k",
                     'messages': content,
                     'temperature': parameter["temperature"],
                     'stream': True,
                     'max_tokens': parameter["max_tokens"],
                     'presence_penalty': parameter["presence_penalty"]}

        if parameter["max_tokens"] == 0:
            json_data.pop("max_tokens")

        response = requests.post(url, headers=headers, json=json_data, stream=True)
    elif model == "perplexity":
        url = api_url
        headers = {
            'Authorization': "Bearer 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",
            'Content-Type': 'application/json',
        }

        json_data = {'model': "perplexity/llama-3.1-sonar-large-128k-chat",
                     'messages': content,
                     'temperature': parameter["temperature"],
                     'stream': True,
                     'max_tokens': parameter["max_tokens"],
                     'presence_penalty': parameter["presence_penalty"]}

        if parameter["max_tokens"] == 0:
            json_data.pop("max_tokens")

        response = requests.post(url, headers=headers, json=json_data, stream=True)
    else:
        url = OPENAI_URL
        key = parameter.get("api_key", OPENAI_KEY)  # 如果存在api_key，使用api_key，否则使用默认的OPENAI_KEY
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}',
            "Accept": "application/json"
        }

        json_data = {'model': parameter["model"],
                     'messages': content,
                     'temperature': parameter["temperature"],
                     'stream': True,
                     'max_tokens': parameter["max_tokens"],
                     'presence_penalty': parameter["presence_penalty"]}

        for i in content:
            if i["role"] == "function" or i.get("function_call"):
                parameter["use_func"] = True
                break
        if parameter.get("use_func"):
            func_dict = {
                'functions': FuncPool.make_func_for_gpt(),  # 使用接口的函数功能则添加
                "function_call": "auto",  # 使用接口的函数功能则添加
            }
            json_data.update(func_dict)

        if parameter["max_tokens"] == 0:
            json_data.pop("max_tokens")

        response = requests.post(url, headers=headers, json=json_data, stream=True)

    return response

data = {
    "parameter": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 0,
        "presence_penalty": 0
    },
    "messages": [
        {
            "content": "你好",
            "role": "user"
        }
    ],
    "presets": {},
}


@bp_send_notoken.route('/send/', methods=['GET'])
def gpt_send():
    unique_key = request.args.get('key')
    try:
        cache_dict = dict(cache.get(unique_key))
        data = cache_dict.get("data")
        cache.delete(unique_key)
    except Exception as e:
        try:
            cache.delete(unique_key)
        except Exception:
            pass
        return make_response(jsonify({
            "status": "error",
            "type": "string",
            "data": "两次接口间超时"
        }), 400)
    if not data.get("dev_func"):
        # 将消息内容发送给GPT并获取返回结果
        model = data["parameter"].get("model", "gpt3")  # 获取模型
        if model == "wenxin":
            api_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token=" + get_access_token()
            # 将消息内容发送给选定的模型并获取返回结果
            gpt_response_generator = generate_response(data["messages"], data["parameter"], api_url, model)
            # 如果GPT返回错误，直接返回内容
            if gpt_response_generator.status_code != 200:
                def generate(result):
                    # 弃用 翻译功能暂时不使用
                    # from src.apps.send.utils import render_error
                    # result, link = render_error(result)
                    # result = "<span style=\"font-weight:900;\">详情请阅读文档</span>: " + f"{link}\n&nbsp;\n" + "```\n" + result + "\n```"
                    result = "```\n" + result + "\n```"
                    result = str(result).replace("\n", "\\n")
                    yield "data: " + result + '\n\n'
                    yield "data: [DONE]\n\n"

                result = gpt_response_generator.text
                headers = {
                    'Content-Type': 'text/event-stream;charset=UTF-8',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',
                    'Transfer-Encoding': 'chunked'}
                return Response(generate(result), mimetype="text/event-stream",
                                headers=headers)
        elif model == "kimi":
            api_url = "https://api.moonshot.cn/v1/chat/completions"
            gpt_response_generator = generate_response(data["messages"], data["parameter"], api_url, model)
            # 如果GPT返回错误，直接返回内容
            if gpt_response_generator.status_code != 200:
                def generate(result):
                    # 弃用 翻译功能暂时不使用
                    # from src.apps.send.utils import render_error
                    # result, link = render_error(result)
                    # result = "<span style=\"font-weight:900;\">详情请阅读文档</span>: " + f"{link}\n&nbsp;\n" + "```\n" + result + "\n```"
                    result = "```\n" + result + "\n```"
                    result = str(result).replace("\n", "\\n")
                    yield "data: " + result + '\n\n'
                    yield "data: [DONE]\n\n"

                result = gpt_response_generator.text
                headers = {
                    'Content-Type': 'text/event-stream;charset=UTF-8',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',
                    'Transfer-Encoding': 'chunked'}
                return Response(generate(result), mimetype="text/event-stream",
                                headers=headers)
        elif model == "perplexity":
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            gpt_response_generator = generate_response(data["messages"], data["parameter"], api_url, model)
            # 如果GPT返回错误，直接返回内容
            if gpt_response_generator.status_code != 200:
                def generate(result):
                    # 弃用 翻译功能暂时不使用
                    # from src.apps.send.utils import render_error
                    # result, link = render_error(result)
                    # result = "<span style=\"font-weight:900;\">详情请阅读文档</span>: " + f"{link}\n&nbsp;\n" + "```\n" + result + "\n```"
                    result = "```\n" + result + "\n```"
                    result = str(result).replace("\n", "\\n")
                    yield "data: " + result + '\n\n'
                    yield "data: [DONE]\n\n"

                result = gpt_response_generator.text
                headers = {
                    'Content-Type': 'text/event-stream;charset=UTF-8',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',
                    'Transfer-Encoding': 'chunked'}
                return Response(generate(result), mimetype="text/event-stream",
                                headers=headers)
        else:
            # 将消息内容发送给选定的模型并获取返回结果
            api_url = ""
            gpt_response_generator = generate_response(data["messages"], data["parameter"], api_url, model)
            # 如果GPT返回错误，直接返回内容
            if gpt_response_generator.status_code != 200:
                def generate(result):
                    # 弃用 翻译功能暂时不使用
                    # from src.apps.send.utils import render_error
                    # result, link = render_error(result)
                    # result = "<span style=\"font-weight:900;\">详情请阅读文档</span>: " + f"{link}\n&nbsp;\n" + "```\n" + result + "\n```"
                    result = "```\n" + result + "\n```"
                    result = str(result).replace("\n", "\\n")
                    yield "data: " + result + '\n\n'
                    yield "data: [DONE]\n\n"

                result = gpt_response_generator.text
                headers = {
                    'Content-Type': 'text/event-stream;charset=UTF-8',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',
                    'Transfer-Encoding': 'chunked'}
                return Response(generate(result), mimetype="text/event-stream",
                                headers=headers)
        # 获取请求头中的 Authorization 字段
        # token = request.headers.get('Authorization')
        # 获取用户token
        token = cache_dict.get("token")
        url = url_for('base.token_prompt.send.computation', _external=True)

        # 使用流式输出的方式处理，这里需要您调用与GPT模型交互的代码，将content传入模型，获取返回结果
        def generate(data, token):
            # 初始化 response_content 字符串
            response_content = ""
            total_characters = 0
            for line in gpt_response_generator.iter_lines():
                if model == "wenxin":
                    if line:
                        decoded_line = line.decode('utf-8')
                        # 处理
                        json_output = decoded_line[6:]
                        output_dict = json.loads(json_output)
                        if output_dict.get("is_end"):
                            output_str = output_dict.get("result")
                            if output_str:
                                yield "data: " + output_str + '\n\n'
                            yield "data: [DONE]\n\n"
                        else:
                            output_dict = json.loads(json_output)
                            output_str = output_dict.get("result")
                        if output_str is None or str(output_str) == "":
                            continue
                        # 获得全部返回内容
                        response_content += str(output_str)
                        # 获得全部返回内容字符数
                        total_characters = len(response_content)
                        output_str = str(output_str).replace("\n", "\\n")
                        yield "data: " + output_str + '\n\n'
                elif model == "kimi":
                    if line:
                        decoded_line = line.decode('utf-8')
                        # 处理
                        json_output = decoded_line[6:]
                        if json_output == '[DONE]':
                            output_str = "[DONE]"
                        else:
                            output_dict = json.loads(json_output)
                            output_str = output_dict.get("choices")[0].get("delta").get("content")
                        if output_str is None or str(output_str) == "":
                            continue
                        # 获得全部返回内容
                        response_content += str(output_str)
                        # 获得全部返回内容字符数
                        total_characters = len(response_content)

                        output_str = str(output_str).replace("\n", "\\n")
                        yield "data: " + output_str + '\n\n'
                elif model == "perplexity":
                    if line:
                        decoded_line = line.decode('utf-8')
                        # 处理
                        json_output = decoded_line[6:]
                        if json_output == '[DONE]':
                            output_str = "[DONE]"
                        else:
                            output_dict = json.loads(json_output)
                            output_str = output_dict.get("choices")[0].get("delta").get("content")
                        if output_str is None or str(output_str) == "":
                            continue
                        # 获得全部返回内容
                        response_content += str(output_str)
                        # 获得全部返回内容字符数
                        total_characters = len(response_content)

                        output_str = str(output_str).replace("\n", "\\n")
                        yield "data: " + output_str + '\n\n'
                else:
                    if line:
                        decoded_line = line.decode('utf-8')
                        # 处理
                        json_output = decoded_line[6:]
                        if json_output == '[DONE]':
                            output_str = "[DONE]"
                        else:
                            output_dict = json.loads(json_output)
                            output_str = output_dict.get("choices")[0].get("delta").get("content")
                        if output_str is None or str(output_str) == "":
                            continue
                        # 获得全部返回内容
                        response_content += str(output_str)
                        # 获得全部返回内容字符数
                        total_characters = len(response_content)

                        output_str = str(output_str).replace("\n", "\\n")
                        yield "data: " + output_str + '\n\n'

            # 创建请求体
            computation_dict = {
                'data': data,
                'total_characters': total_characters,
                'response_content': response_content
            }
            requests.post(
                url,
                json=computation_dict,
                headers={
                    "Authorization": token
                }
            )

        headers = {
            'Content-Type': 'text/event-stream;charset=UTF-8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Transfer-Encoding': 'chunked'
        }

        return Response(generate(data, token), mimetype="text/event-stream",
                        headers=headers)

    # # 在发送给OpenAI之前，判断是否是请求调用函数，如果是，则直接调用函数，并返回对应的响应
    # latest_message = data["messages"][-1].get('function_call')
    # if latest_message:
    #     def generate(result):
    #         result = "```\n" + result + "\n```"
    #         result = str(result).replace("\n", "\\n")
    #         yield "data: " + result + '\n\n'
    #         yield "data: [DONE]auto\n\n"
    #
    #     headers = {
    #         'Content-Type': 'text/event-stream;charset=UTF-8',
    #         'Cache-Control': 'no-cache',
    #         'Connection': 'keep-alive',
    #         'X-Accel-Buffering': 'no',
    #         'Transfer-Encoding': 'chunked'}
    #
    #     func_name = latest_message.get('name')
    #     if not func_name in FuncPool.func_list:
    #         result_str = f"函数名错误：无{func_name}()函数"
    #         return Response(generate(result_str), mimetype="text/event-stream",
    #                         headers=headers)
    #     args_dict = json.loads(latest_message.get('arguments'))
    #     output_str = FuncPool.call_func(func_name, args_dict)
    #     result_str = json.dumps({
    #         "is_func": True,
    #         "message": {
    #             "role": "function",
    #             "name": func_name,
    #             "content": output_str
    #         }
    #     })
    #
    #     return Response(generate(result_str), mimetype="text/event-stream",
    #                     headers=headers)
    #
    # # 将消息内容发送给GPT并获取返回结果
    # model = data["parameter"].get("model", "gpt3")  # 获取模型
    #
    # if model == "wenxin":
    #     api_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token=" + get_access_token()
    # # 将消息内容发送给选定的模型并获取返回结果
    #     gpt_response_generator = generate_response(data["messages"], data["parameter"], api_url, model)
    # elif model == "kimi":
    #     api_url = "https://api.moonshot.cn/v1/chat/completions"
    #     gpt_response_generator = generate_response(data["messages"], data["parameter"], api_url, model)
    #     # 如果GPT返回错误，直接返回内容
    #     if gpt_response_generator.status_code != 200:
    #         def generate(result):
    #             # 弃用 翻译功能暂时不使用
    #             # from src.apps.send.utils import render_error
    #             # result, link = render_error(result)
    #             # result = "<span style=\"font-weight:900;\">详情请阅读文档</span>: " + f"{link}\n&nbsp;\n" + "```\n" + result + "\n```"
    #
    #             result = "```\n" + result + "\n```"
    #             result = str(result).replace("\n", "\\n")
    #             yield "data: " + result + '\n\n'
    #             yield "data: [DONE]\n\n"
    #
    #         result = gpt_response_generator.text
    #         headers = {
    #             'Content-Type': 'text/event-stream;charset=UTF-8',
    #             'Cache-Control': 'no-cache',
    #             'Connection': 'keep-alive',
    #             'X-Accel-Buffering': 'no',
    #             'Transfer-Encoding': 'chunked'}
    #         return Response(generate(result), mimetype="text/event-stream",
    #                         headers=headers)
    #         # # 示例
    #         # {
    #         #     "error": {
    #         #         "message": "'messages' is a required property",
    #         #         "type": "invalid_request_error",
    #         #         "param": null,
    #         #         "code": null
    #         #     }
    #         # }
    # else:
    #     api_url=""
    #     gpt_response_generator = generate_response(data["messages"], data["parameter"], api_url, model)
    # # 如果GPT返回错误，直接返回内容
    #     if gpt_response_generator.status_code != 200:
    #         def generate(result):
    #             # 弃用 翻译功能暂时不使用
    #             # from src.apps.send.utils import render_error
    #             # result, link = render_error(result)
    #             # result = "<span style=\"font-weight:900;\">详情请阅读文档</span>: " + f"{link}\n&nbsp;\n" + "```\n" + result + "\n```"
    #
    #             result = "```\n" + result + "\n```"
    #             result = str(result).replace("\n", "\\n")
    #             yield "data: " + result + '\n\n'
    #             yield "data: [DONE]\n\n"
    #
    #         result = gpt_response_generator.text
    #         headers = {
    #             'Content-Type': 'text/event-stream;charset=UTF-8',
    #             'Cache-Control': 'no-cache',
    #             'Connection': 'keep-alive',
    #             'X-Accel-Buffering': 'no',
    #             'Transfer-Encoding': 'chunked'}
    #         return Response(generate(result), mimetype="text/event-stream",
    #                         headers=headers)
    #         # # 示例
    #         # {
    #         #     "error": {
    #         #         "message": "'messages' is a required property",
    #         #         "type": "invalid_request_error",
    #         #         "param": null,
    #         #         "code": null
    #         #     }
    #         # }
    #
    # # 获取请求头中的 Authorization 字段
    # # token = request.headers.get('Authorization')
    # # 获取用户token
    # token = cache_dict.get("token")
    # url = url_for('base.token_prompt.send.computation', _external=True)
    #
    # # 使用流式输出的方式处理，这里需要您调用与GPT模型交互的代码，将content传入模型，获取返回结果
    # def generate(data, token):
    #     # 初始化 response_content 字符串
    #     response_content = ""
    #     total_characters = 0
    #     function_name = ""  # 用于存放OpenAI想要调用的函数名称
    #     for line in gpt_response_generator.iter_lines():
    #         if model == "wenxin":
    #             if line:
    #                 decoded_line = line.decode('utf-8')
    #                 # 处理
    #                 json_output = decoded_line[6:]
    #                 output_dict = json.loads(json_output)
    #                 if output_dict.get("is_end"):  # SSE结束
    #                     output_str = "[DONE]auto" if function_name else "[DONE]"
    #                     yield "data: " + output_str + '\n\n'
    #                     continue
    #                 output_dict = json.loads(json_output)
    #                 output_str = output_dict.get("result")
    #                 response_content += str(output_str)  # 获得全部返回内容
    #                 total_characters = len(response_content)  # 获得全部返回内容字符数
    #
    #                 output_str = str(output_str).replace("\n", "\\n")
    #
    #                 result_str = json.dumps({
    #                         "message": {
    #                             "role": "assistant",
    #                             "content": output_str
    #                         }
    #                     })
    #                 yield "data: " + output_str + '\n\n'
    #                 continue
    #         elif model == "kimi":
    #             if line:
    #                 decoded_line = line.decode('utf-8')
    #                 # 处理
    #                 json_output = decoded_line[6:]
    #                 if json_output == '[DONE]':  # SSE结束
    #                     output_str = "[DONE]auto" if function_name else "[DONE]"
    #                     yield "data: " + output_str + '\n\n'
    #                     continue
    #
    #                 output_dict = json.loads(json_output)
    #                 # if not output_dict.get("choices")[0].get("delta"):  # 正文内容为空，倒数第二条
    #                 #     continue
    #                 #
    #                 # if output_dict.get("choices")[0].get("delta").get('function_call'):  # 请求函数的消息
    #                 #     if output_dict.get("choices")[0].get("delta").get("function_call").get('name'):
    #                 #         function_name = output_dict.get("choices")[0].get("delta").get("function_call").get('name')
    #                 #     output_str = output_dict.get("choices")[0].get("delta").get("function_call").get('arguments')
    #                 #     response_content += str(output_str)  # 获得全部返回内容
    #                 #     total_characters = len(response_content)  # 获得全部返回内容字符数
    #                 #
    #                 #     output_str = str(output_str).replace("\n", "\\n")
    #                 #
    #                 #     result_str = json.dumps({
    #                 #         "is_func": True,
    #                 #         "message": {
    #                 #             "role": "assistant",
    #                 #             "content": None,
    #                 #             "function_call": {
    #                 #                 "name": function_name,
    #                 #                 "arguments": output_str
    #                 #             }
    #                 #         }
    #                 #     })
    #                 #     yield "data: " + result_str + '\n\n'
    #                 #     continue
    #                 # else:  # 回复消息
    #                 output_str = output_dict.get("choices")[0].get("delta").get("content")
    #                 response_content += str(output_str)  # 获得全部返回内容
    #                 total_characters = len(response_content)  # 获得全部返回内容字符数
    #
    #                 output_str = str(output_str).replace("\n", "\\n")
    #
    #                 result_str = json.dumps({
    #                         "message": {
    #                             "role": "assistant",
    #                             "content": output_str
    #                         }
    #                     })
    #                 yield "data: " + output_str + '\n\n'
    #                 continue
    #         else:
    #             if line:
    #                 decoded_line = line.decode('utf-8')
    #                 # 处理
    #                 json_output = decoded_line[6:]
    #                 if json_output == '[DONE]':  # SSE结束
    #                     output_str = "[DONE]auto" if function_name else "[DONE]"
    #                     yield "data: " + output_str + '\n\n'
    #                     continue
    #
    #                 output_dict = json.loads(json_output)
    #
    #                 if not output_dict.get("choices")[0].get("delta"):  # 正文内容为空，倒数第二条
    #                     continue
    #
    #                 if output_dict.get("choices")[0].get("delta").get('function_call'):  # 请求函数的消息
    #                     if output_dict.get("choices")[0].get("delta").get("function_call").get('name'):
    #                         function_name = output_dict.get("choices")[0].get("delta").get("function_call").get('name')
    #                     output_str = output_dict.get("choices")[0].get("delta").get("function_call").get('arguments')
    #                     response_content += str(output_str)  # 获得全部返回内容
    #                     total_characters = len(response_content)  # 获得全部返回内容字符数
    #
    #                     output_str = str(output_str).replace("\n", "\\n")
    #
    #                     result_str = json.dumps({
    #                         "is_func": True,
    #                         "message": {
    #                             "role": "assistant",
    #                             "content": None,
    #                             "function_call": {
    #                                 "name": function_name,
    #                                 "arguments": output_str
    #                             }
    #                         }
    #                     })
    #                     yield "data: " + result_str + '\n\n'
    #                     continue
    #                 else:  # 回复消息
    #                     output_str = output_dict.get("choices")[0].get("delta").get("content")
    #                     response_content += str(output_str)  # 获得全部返回内容
    #                     total_characters = len(response_content)  # 获得全部返回内容字符数
    #
    #                     output_str = str(output_str).replace("\n", "\\n")
    #
    #                     result_str = json.dumps({
    #                         "message": {
    #                             "role": "assistant",
    #                             "content": output_str
    #                         }
    #                     })
    #                     yield "data: " + result_str + '\n\n'
    #                     continue
    #     # 循环结束
    #     # 创建请求体
    #     computation_dict = {
    #         'data': data,
    #         'total_characters': total_characters,
    #         'response_content': response_content
    #     }
    #     requests.post(
    #         url,
    #         json=computation_dict,
    #         headers={
    #             "Authorization": token
    #         }
    #     )
    #
    # headers = {
    #     'Content-Type': 'text/event-stream;charset=UTF-8',
    #     'Cache-Control': 'no-cache',
    #     'Connection': 'keep-alive',
    #     'X-Accel-Buffering': 'no',
    #     'Transfer-Encoding': 'chunked'
    # }
    #
    # return Response(generate(data, token), mimetype="text/event-stream",
    #                 headers=headers)
