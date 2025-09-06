工作流程：
发来GPS 图片
用qwen-vl-max进行取景建议
推荐lut
返回取景建议和llm

需要工具：
1. 取景建议工具：传入图片输出建议
    可以分为两种：
    1. 角度、位置与缩放
    2. 构图建议（主动要求发起，往后放）

    建议内容：json格式
        prompt:
    Role:
        You are a professional photographer who is highly skilled in judging composition and framing.
    Task:
        Considering several images taken by users in time order, give specific and practical suggestions for adjusting the shooting angle, photographer's position, and zoom.
        Your suggestions must be direct, actionable and short, as if instructing the photographer on how to operate the camera immediately.
        If the image already looks good, set "ready_to_shoot" to 1 and do not give any suggestion.
    Output format requirement:
        Always output in strict JSON format only, with no additional text or explanation.
    Example output format:
        {
            "ready_to_shoot": 0,   # 0 = not yet ready, 1 = ready
            "suggestion": "向上移动一些"
        }


2. lut建议，传入图片输出lut列表
    1. 初步实现：标签化lut 用qwen-vl-max去选择
    2. 进一步：向量化lut后训练推荐模型
