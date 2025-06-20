import json
from talker.models import TalkSession
from talker.api import VivoGPT, VivoGPTError


def analyze_and_update_talksession(session: TalkSession):
    """
    自动分析会话历史并根据大模型回复自动更新 TalkSession 的各属性。
    :param session: TalkSession 实例
    :return: (success, message)
    """
    # 1. 获取历史记录
    history = session.history or []
    # 2. 组装 prompt 输入
    prompt_input = json.dumps(history, ensure_ascii=False)
    # 3. 调用大模型（controller 预设）
    client = VivoGPT()
    try:
        # controller prompt 已在 prompts.json 配置
        prompt = f"输入：{prompt_input}"
        response = client.chat(prompt, type="controller")
        content = response.get("data", {}).get("content", "")
        # 4. 解析大模型回复
        result = json.loads(content)
        # 5. 自动更新 TalkSession
        session.budget = result.get("budget")
        session.locations = result.get("locations", [])
        session.start_date = result.get("start_date")
        session.end_date = result.get("end_date")
        session.state = result.get("state", {})
        session.save()
        return True, "会话信息已自动分析并更新"
    except VivoGPTError as e:
        return False, f"大模型API错误: {e.message}"
    except Exception as e:
        return False, f"自动分析或更新失败: {str(e)}"
