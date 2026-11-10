#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oogiri Benchmark Evaluation Runner for External Models
Supports true multi-agent subagent pipeline (A/B/C tracks + Stage 2 prosecutor adjudication)
via OpenAI-compatible Chat Completions API.
"""

import os
import sys
import json
import base64
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 24 Secular Domains
SECULAR_DOMAINS = [
    "市政危房维保", "临期商超早市", "驾校科目考场", "急诊老年康养",
    "城中村租房中介", "民政婚姻登记", "海关安检清关", "殡葬法事公墓",
    "县城草台剧组", "典当行拍卖", "餐饮后厨卫生", "业委会物业纠纷",
    "古董文玩鉴定", "宠物绝育检疫", "长途货运治超", "废品回收拆解",
    "澡堂足疗技师", "公园象棋摊", "农贸水产批发", "裁缝铺改衣",
    "修锁配钥匙", "广场舞音响", "老式国营食堂", "高速收费站"
]

CONFIGS = {
    "gpt-6-astra": {
        "url": "https://api-direct.ccapi.us/v1/chat/completions",
        "key": os.environ.get("CCAPI_KEY_GPT6", ""),
        "model": "gpt-6-astra"
    },
    "claude-opus-5-5": {
        "url": "https://api-direct.ccapi.us/v1/chat/completions",
        "key": os.environ.get("CCAPI_KEY_CLAUDE", ""),
        "model": "claude-opus-5-5"
    }
}

def call_llm(model_cfg, messages, max_tokens=1500, temperature=0.7):
    headers = {
        "Authorization": f"Bearer {model_cfg['key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_cfg["model"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    for attempt in range(3):
        try:
            r = requests.post(model_cfg["url"], json=payload, headers=headers, timeout=120)
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"Error {r.status_code}: {r.text[:100]} (attempt {attempt+1})", file=sys.stderr)
        except Exception as e:
            print(f"Request failed: {e} (attempt {attempt+1})", file=sys.stderr)
    return ""

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def build_user_content(prompt_text, image_path=None):
    if image_path and os.path.exists(image_path):
        b64 = encode_image(image_path)
        return [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]
    return prompt_text

def run_zero_shot(model_cfg, item):
    prompt_intro = "你正在参加日式大喜利（Oogiri）比赛。请针对以下题目，直接给出一句最具幽默感、爆笑且有日式大喜利风格的吐槽回答。直接输出一句短句，严格在8到14字之间，不带任何标点符号，不要多余解释：\n"
    content = build_user_content(prompt_intro + item["prompt"], item.get("image_path"))
    msgs = [{"role": "user", "content": content}]
    return call_llm(model_cfg, msgs, max_tokens=100, temperature=0.8)

def run_oogiri_pipeline(model_cfg, item):
    """真正的多Agent三轨发散 + 公诉人证伪重铸流程"""
    prompt_str = item["prompt"]
    image_path = item.get("image_path")
    
    # Stage 0: 提取平庸基线与地基切片
    stage0_prompt = (
        f"【日式大喜利 Stage 0 地基遥测与平庸基线】\n"
        f"命题：{prompt_str}\n"
        f"请提取大众在1秒内最容易想到的3条合情合理但毫无幽默感的字面解释或现实观察（作为全场禁止触碰的负向基线）。\n"
        f"输出格式：直接输出3行，每行一条平庸基线短句。"
    )
    stage0_content = build_user_content(stage0_prompt, image_path)
    forbidden_baseline = call_llm(model_cfg, [{"role": "user", "content": stage0_content}], max_tokens=200)

    # Stage 1: 三轨独立子 Agent 并行派发
    prompt_a = (
        f"【命题】{prompt_str}\n"
        f"【先导词】：体面破绽\n"
        f"【认知机制】：从原题自带的专属器物、服装或仪式出发，锁定角色极力维持的高贵、专业或强悍排场，写出他为了省钱、惜物、凑合或怕赔钱而做出的寒酸小动作。全句纯粹由原题实物名词与具体生活动作构成。\n"
        f"【语言规范】严格8到14字之间，客观描述具体动作与实物，不带标点符号。\n"
        f"【负向排除集】避开平庸基线：\n{forbidden_baseline}\n"
        f"【交付】输出3句短句，每行一句。"
    )
    
    domains_formatted = " | ".join(f"[{i+1} {d}]" for i, d in enumerate(SECULAR_DOMAINS))
    prompt_b = (
        f"【命题】{prompt_str}\n"
        f"【24类世俗大域】：{domains_formatted}\n"
        f"【先导词】：异业动作\n"
        f"【认知机制】：对照24个世俗大域逐类发散。提取每个大域里连三岁小孩都能一秒认出的「标志性日常动作、习惯性口头禅或肌肉记忆」，错位安插到原题角色或器物上。只用通俗生活动作词，避开生僻专业术语。\n"
        f"【语言规范】每句严格8到14字之间，直接描述原题角色做出的异业动作，不带标点符号。\n"
        f"【负向排除集】避开平庸基线：\n{forbidden_baseline}\n"
        f"【交付】严格按 `[序号 类别名] 台词` 格式输出全部24句。"
    )
    
    prompt_c = (
        f"【命题】{prompt_str}\n"
        f"【先导词】：物理死磕\n"
        f"【认知机制】：严守在原题世界观内部，顺着事物的天然物理属性（长度、温度、重量、弹性形变、时间累积）往极端的因果逻辑顺推一步，或做千倍空间尺度的放大与缩小。只用朴素日常实物词与自然物理法则，展现冷酷荒谬。\n"
        f"【语言规范】严格8到14字之间，像陈述客观自然法则一样平铺直叙，不带标点符号。\n"
        f"【负向排除集】避开平庸基线：\n{forbidden_baseline}\n"
        f"【交付】输出3句短句，每行一句。"
    )

    with ThreadPoolExecutor(max_workers=3) as executor:
        f_a = executor.submit(call_llm, model_cfg, [{"role": "user", "content": build_user_content(prompt_a, image_path)}], 300)
        f_b = executor.submit(call_llm, model_cfg, [{"role": "user", "content": build_user_content(prompt_b, image_path)}], 1200)
        f_c = executor.submit(call_llm, model_cfg, [{"role": "user", "content": build_user_content(prompt_c, image_path)}], 300)
        out_a = f_a.result()
        out_b = f_b.result()
        out_c = f_c.result()

    # Stage 2: 公诉人统一质检与终选总冠军
    stage2_prompt = (
        f"【日式大喜利 Stage 2 公诉人统一裁决与腰斩重铸】\n"
        f"原命题：{prompt_str}\n"
        f"禁止触碰的平庸基线：\n{forbidden_baseline}\n\n"
        f"【Subagent A (体面破绽) 候选】：\n{out_a}\n\n"
        f"【Subagent B (异业动作 24域) 候选】：\n{out_b}\n\n"
        f"【Subagent C (物理死磕) 候选】：\n{out_c}\n\n"
        f"【公诉人审查铁律】：\n"
        f"1. 淘汰与平庸基线重合者；\n"
        f"2. 针对B轨24条，淘汰生搬硬套外来假道具、需要行业知识解码的冷门词（淘汰率>85%），仅留与原题动作严丝合缝的Top 1~2；\n"
        f"3. 单格漫画分镜检验：必须能脑补出具体画面；\n"
        f"4. 腰斩剪枝：若去掉后半句多余说明词能让包袱更脆，直接砍除。\n\n"
        f"请直接给出：\n"
        f"1. 本题【全场总冠军金句】（严格8~14字，纯汉字字母数字，零标点符号，底词右置）；\n"
        f"2. 简短公诉人裁决胜出理由（50字以内）。\n"
        f"格式严格如下：\n"
        f"全场总冠军：<金句>\n"
        f"胜出理由：<理由>"
    )
    stage2_content = build_user_content(stage2_prompt, image_path)
    stage2_out = call_llm(model_cfg, [{"role": "user", "content": stage2_content}], max_tokens=400)
    
    champion = ""
    reason = ""
    for line in stage2_out.splitlines():
        if "全场总冠军" in line:
            champion = line.split("：")[-1].split(":")[-1].strip().replace("`", "").replace("“", "").replace("”", "").replace('"', "")
        elif "胜出理由" in line:
            reason = line.split("：")[-1].split(":")[-1].strip()
    
    if not champion and stage2_out:
        champion = stage2_out.splitlines()[0].strip()

    return {
        "champion": champion,
        "reason": reason,
        "raw_stage2": stage2_out,
        "out_a": out_a,
        "out_b": out_b,
        "out_c": out_c
    }

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["gpt-6-astra", "claude-opus-5-5", "all"], default="all")
    args = parser.parse_args()

    # Load benchmark dataset（本地私有库，路径不进仓库：用环境变量提供）
    benchmark_path = os.environ.get("OOGIRI_BENCHMARK_PATH", "")
    if not benchmark_path or not os.path.isfile(benchmark_path):
        raise SystemExit(
            "缺少基准题库：请设置环境变量 OOGIRI_BENCHMARK_PATH 指向 benchmark_dataset.json"
            "（位于本地 oogiri-flow skill 的 resources/ 目录）。"
        )
    with open(benchmark_path, "r", encoding="utf-8") as f:
        items = json.load(f)[:10] # first 10 items (T01~T07, P01~P03)

    target_models = ["gpt-6-astra", "claude-opus-5-5"] if args.model == "all" else [args.model]

    missing = [m for m in target_models if not CONFIGS[m]["key"]]
    if missing:
        raise SystemExit(
            "缺少 API Key 环境变量：" + ", ".join(
                {"gpt-6-astra": "CCAPI_KEY_GPT6", "claude-opus-5-5": "CCAPI_KEY_CLAUDE"}[m] for m in missing
            ) + "\n请在 shell 里设置后重跑；本仓库是公开的，绝对不要把 key 写回这个文件。"
        )

    for model_name in target_models:
        cfg = CONFIGS[model_name]
        print(f"\n==========================================")
        print(f"   STARTING EVALUATION: {model_name}")
        print(f"==========================================")
        
        results = []
        for idx, item in enumerate(items, 1):
            qid = item["id"]
            qtype = item["type"]
            prompt = item["prompt"]
            print(f"\n[{model_name}] Processing {qid} ({idx}/10): {prompt[:30]}...")
            
            # 1. Zero-shot
            zero_shot_res = run_zero_shot(cfg, item)
            print(f"  -> Zero-shot: {zero_shot_res}")
            
            # 2. Oogiri-flow
            flow_res = run_oogiri_pipeline(cfg, item)
            print(f"  -> Oogiri-Flow Champion: {flow_res['champion']}")
            print(f"     Reason: {flow_res['reason']}")
            
            results.append({
                "id": qid,
                "type": qtype,
                "prompt": prompt,
                "image_path": item.get("image_path", ""),
                "zero_shot": zero_shot_res,
                "flow": flow_res
            })
            
        # Save output JSON
        out_json_path = f"eval_{model_name.replace('-', '_')}.json"
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[Saved JSON]: {out_json_path}")

if __name__ == "__main__":
    main()
