import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from talker.models import TalkSession
from talker.api import VivoGPT, VivoGPTError
import logging

def extract_json(content):
    """提取第一个 {...} 之间的内容，返回纯 JSON 字符串"""
    if not content:
        return content
    match = re.search(r'\{[\s\S]*\}', content)
    if match:
        return match.group(0)
    return content.strip()

def _call_extract(client, prompt_type, history):
    prompt = f"输入：{json.dumps(history, ensure_ascii=False)}"
    try:
        response = client.chat(prompt, type=prompt_type)
        content = response.get("data", {}).get("content", "")
        return prompt_type, content, None
    except Exception as e:
        logging.error(f"extract {prompt_type} 失败: {e}")
        return prompt_type, None, str(e)

def analyze_and_update_talksession(session: TalkSession):
    """
    并行分析会话历史，综合大模型结果，自动更新 TalkSession。
    :param session: TalkSession 实例
    :return: (success, message)
    """
    history = session.history or []
    client = VivoGPT()
    extract_types = [
        "extract_budget",
        "extract_locations",
        "extract_dates",
        "extract_user_profile"
    ]
    extract_results = {}
    errors = {}
    # 1. 并行发送 extract 任务（不含state）
    with ThreadPoolExecutor() as executor:
        future_to_type = {
            executor.submit(_call_extract, client, t, history): t for t in extract_types
        }
        for future in as_completed(future_to_type):
            t = future_to_type[future]
            _, content, err = future.result()
            print(f"[DEBUG] 大模型extract任务 {t} 返回: {content}")
            # 处理 markdown 代码块包裹的 json，并提取 {...}
            if content:
                content = extract_json(content)
            if err:
                errors[t] = err
                extract_results[t] = None
            else:
                try:
                    extract_results[t] = json.loads(content) if content else None
                except Exception as e:
                    errors[t] = f"extract结果解析失败: {e}"
                    extract_results[t] = None
    if errors:
        logging.warning(f"extract 阶段部分失败: {errors}")
    # 2. 用 format_constraint prompt 格式化3个结果
    format_input = {
        "budget": extract_results.get("extract_budget"),
        "locations": extract_results.get("extract_locations"),
        "start_date": None,
        "end_date": None
    }
    dates = extract_results.get("extract_dates")
    if dates:
        format_input["start_date"] = dates.get("start_date")
        format_input["end_date"] = dates.get("end_date")
    format_prompt = f"输入：{json.dumps(format_input, ensure_ascii=False)}"
    try:
        response = client.chat(format_prompt, type="format_constraint")
        content = response.get("data", {}).get("content", "")
        print(f"[DEBUG] 大模型format_constraint返回: {content}")
        # 处理 markdown 代码块包裹的 json，并提取 {...}
        if content:
            content = extract_json(content)
        result = json.loads(content)
        # 字段校验，防止污染
        session.budget = result.get("budget") if isinstance(result.get("budget", None), (int, float, type(None))) else None
        session.locations = result.get("locations") if isinstance(result.get("locations", None), list) else []
        session.start_date = result.get("start_date") if isinstance(result.get("start_date", None), str) else None
        session.end_date = result.get("end_date") if isinstance(result.get("end_date", None), str) else None
        # 新增：自动更新用户画像
        user_profile = extract_results.get("extract_user_profile")
        session.user_profile = user_profile if isinstance(user_profile, dict) else {}
        session.save()
    except VivoGPTError as e:
        logging.error(f"format_constraint 阶段大模型API错误: {e.message}")
        return False, f"大模型API错误: {e.message}，extract阶段错误: {errors if errors else '无'}"
    except Exception as e:
        logging.error(f"format_constraint 阶段异常: {e}")
        return False, f"自动分析或更新失败: {str(e)}，extract阶段错误: {errors if errors else '无'}"
    # 3. 单独处理 state
    try:
        state = extract_state(session, history, extract_results)
        session.state = state if isinstance(state, dict) else {}
        session.save()
    except Exception as e:
        logging.error(f"extract_state 阶段异常: {e}")
        return False, f"state处理失败: {str(e)}"
    msg = "会话信息已自动分析并更新"
    if errors:
        msg += f"，但部分extract任务失败: {errors}"
    return True, msg

def extract_state(session, history, extract_results):
    """
    占位方法：请在此实现你的 state 处理逻辑
    """
    # TODO: 实现自定义 state 处理逻辑
    return {}
