import time
import requests
from openai import OpenAI
from docx import Document
import os
from utils import Utils
# 该类用于保存大模型的基本信息、与大模型对话
class LLMTool:
    # deepseek的密钥
    api_key = ""
    # deepseek的api
    api_url = "https://api.deepseek.com"

    # aliyun的密钥
    aliyun_api_key = "sk-5c1b94996a5a4b219a9552ff9fe56f24"
    # aliyun的api
    aliyun_api_url = ""
    def __init__(self):
        self.messages = [
      
       
    ]
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)
        self.is_rq_added = False

    # 与大模型交互
    def chat_with_qwen(self, file_path, user_message,ai_response_path):
         # 记录函数开始运行时间
        start_time = time.time()
        client = OpenAI(api_key=self.aliyun_api_key, base_url=self.aliyun_api_url)

        # 添加用户消息
        self.messages.append({"role": "user", "content": user_message})
        if len(file_path) > 0:
            with open(file_path, "rb") as file:
                self.messages.append({"role": "user", "content": file.read().decode("utf-8")})

        completion = client.chat.completions.create(
            model="qwen-max",  
            messages=  self.messages
        )
        ai_response = completion.choices[0].message.content
        # 获取本轮对话的token数
        token_num = completion.usage.total_tokens
        print(f"本轮对话总token数: {token_num}")
        self.messages.append({"role": "assistant", "content": ai_response})

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"本轮对话时间: {elapsed_time:.2f}秒")
        # 将运行时间和AI回复保存到指定文件中,用utf-8编码
        with open(ai_response_path, "a", encoding="utf-8") as f:
            f.write(f"本轮对话时间: {elapsed_time:.2f}秒\n")
            f.write(f"本轮对话总token数: {token_num}\n")
            f.write(f"AI回复: {ai_response}\n")
            f.write("-" * 50 + "\n")
        return ai_response

    # 添加文件与ds交互
    def chat_with_file(self, ai_response_path, file_path=None, user_message=None, error_times=0):
        # 记录函数开始运行时间
        start_time = time.time()

        # 添加提示词
        if user_message is not None:
                    self.messages.append({"role": "user", "content": user_message})
        # 添加需求文件的文本内容
        if self.is_rq_added == False and file_path is not None:
            self.is_rq_added = True
            rq_text = ""
            if file_path.endswith('.txt'):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.messages.append({"role": "user", "content": f.read()})
            else:

                rq_text = Utils.docx_to_text(file_path)
                self.messages.append({"role": "user", "content": rq_text})


        # if len(file_path) > 0:
        #     with open(file_path, "rb") as file:
        #         self.messages.append({"role": "user", "content": file.read().decode("utf-8")})

        # 构造请求体
        # payload = {
        #     "model": "deepseek-chat",
        #     "messages": self.messages,
        # }
        # response = requests.post(self.api_url, headers=headers, json=payload)
       
        completion = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=self.messages
        )
        # 获取AI回复并存储
        token_num = completion.usage.total_tokens
        print(f"本轮对话总token数: {token_num}")
        ai_response = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": ai_response})

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"本轮对话时间: {elapsed_time:.2f}秒")
        # 将运行时间和AI回复保存到指定文件中,用utf-8编码
        # 创建目录（如果不存在的话）
        os.makedirs(os.path.dirname(ai_response_path), exist_ok=True)
        with open(ai_response_path, "a", encoding="utf-8") as f:
            f.write(f"本轮对话时间: {elapsed_time:.2f}秒\n")
            f.write(f"本轮对话总token数: {token_num}\n")
            # 记录当前系统名称
            f.write(f"{file_path}\n")
            # 记录当前错误次数
            f.write(f"当前脚本错误次数：{error_times}\n")
            f.write(f"AI回复: {ai_response}\n")
            f.write("-" * 50 + "\n")
        # 保存思维链的内容
        with open(f"{ai_response_path}_chain.txt", "a", encoding="utf-8") as f:
            f.write(f"思维链内容:\n{completion.choices[0].message.reasoning_content}\n")
        
        return
    
    # 保存整个对话为json
    def save_chat_history(self, save_path):
        import json
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)

    # 历史对话
    def chat_with_history(self, history_messages, ai_response_path):
        # 记录函数开始运行时间
        start_time = time.time()
        # 清空当前消息
        self.messages = []
        # 添加历史消息
        for msg in history_messages:
            self.messages.append(msg)
        # 发送请求
        completion = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=self.messages
        )
        # 获取AI回复并存储
        token_num = completion.usage.total_tokens
        print(f"本轮对话总token数: {token_num}")
        ai_response = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": ai_response})

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"本轮对话时间: {elapsed_time:.2f}秒")
        # 将运行时间和AI回复保存到指定文件中,用utf-8编码
        with open(ai_response_path, "a", encoding="utf-8") as f:
            f.write(f"本轮对话时间: {elapsed_time:.2f}秒\n")
            f.write(f"本轮对话总token数: {token_num}\n")
            f.write(f"AI回复: {ai_response}\n")
            f.write("-" * 50 + "\n")



    # 拆分信息块
    def split_message(self, message, max_length=4096):
        # 按照最大长度拆分消息
        return [message[i:i + max_length] for i in range(0, len(message), max_length)]
