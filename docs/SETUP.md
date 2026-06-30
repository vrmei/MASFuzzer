# D5 实验环境配置（security-oriented MAS fuzz）

> Fork 专用：只管 D5。核心结论——**D5 是 API 绑定的,GPU 非必需**;一张 24GB 卡推荐用于本地开源 Worker +
> oracle embedder + 未来 D1-steering 融合。骨架已在 `direction_5/mve_skeleton/`(mock 已跑通),实验=把 mock 换真模型。

## 1. 为什么 GPU 不是硬需求
D5 的 MAS 本身 = 一串 LLM agent 调用。Manager/Worker/oracle-judge 都可走 **OpenRouter API**;fuzz 循环
(mutate → 跑 MAS → oracle 判定 → 报告)是编排 + 文本处理,主要吃 **CPU + 网络 + API 额度**,不吃显存。
GPU 只在三种情况才需要:(a) 想本地跑开源 Worker 省 API/可复现;(b) goal-hijack oracle 想用本地 embedding;
(c) 把 **D1 的 steering 作为一个 mutation 算子**(需激活 hook → 必须本地开源模型)。

## 2. 推荐三档配置

| 档 | 硬件 | 适用 | 说明 |
|---|---|---|---|
| **最小(v1 起步)** | 无 GPU,普通 CPU 机(16GB+ RAM)+ 网络 | API-only 黑盒核心 | 直接把骨架的 MockLLM 换成 OpenRouter 客户端即可跑通完整 fuzz 闭环。**最快上手路径。** |
| **推荐** | **1× RTX 4090 (24GB)** + 32GB RAM + ~100GB 磁盘 | 本地开源 Worker + 本地 oracle embedder | 你已有 AutoDL 4090 盒,用一台即可。8B 级 Worker 跑得很舒服。 |
| **融合/扩展(可选,后期)** | 1× A100-80GB(或 2×4090 带 offload) | 70B 级本地 Worker,或 D1-steering 上更大模型 | 仅当要把 steering 算子上 70B,或要本地高保真复现时。 |

**R1(DeepSeek-R1,671B MoE):一律走 API,不要本地。** 作黑盒 Worker 用 OpenRouter 即可。

## 3. 要不要下载模型?

**API-only 路径:基本不用下载**(R1 / DeepSeek-V3 / GPT-4o-mini 全走 OpenRouter)。唯一可选下个小 embedding 模型。

**本地开源 Worker 路径(推荐),下这些:**

| 模型 | HF id | 显存 fp16 / 4-bit | 必需? | 用途 |
|---|---|---|---|---|
| Llama-3.1-8B-Instruct | `meta-llama/Llama-3.1-8B-Instruct` | ~16GB / ~6GB | 推荐 | 廉价可复现 Worker;**D1 融合时取激活** |
| Qwen2.5-7B-Instruct | `Qwen/Qwen2.5-7B-Instruct` | ~15GB / ~6GB | 可选 | 第二个开源 Worker,做能力分档 |
| Llama-Guard-3-8B | `meta-llama/Llama-Guard-3-8B` | ~16GB | 可选 | guard baseline / 安全判官 |
| bge-small-en-v1.5 | `BAAI/bge-small-en-v1.5` | <1GB(CPU 即可) | 推荐 | goal-hijack oracle(原始目标 vs 达成状态的 embedding 相似度) |

- 三档同卡不能并存;24GB 一次跑一个 8B + 一个小 embedder 没问题。
- gated Llama 需 HF token;HF cache 沿用 `Z:\study\project\AS\hf_cache`。

## 4. 要拿的代码/数据(不是模型)

- [ ] **FLARE**(arXiv 2604.05289)代码 + 它的 **16 个开源 MAS app** —— ⚠️ **artifact 是否公开本轮未确认,先去 GitHub/arXiv 核**。若未开源,fallback = 用 AutoGen / CrewAI / MetaGPT 的示例 app 自组一套可比的 MAS 集(写进 data_availability)。
- [ ] **AgentFuzzer / AgentVigil**(arXiv 2505.05849,Dawn Song 组)代码 —— 单 agent 安全 fuzz **baseline**,同样先确认是否开源。
- [ ] 母论文的 **AutoGen Manager-Worker pipeline + 500-样本 gated benchmark + Grade≥2 oracle rubric** —— 你们自有(已确认可用)。
- [ ] 现成骨架:`direction_5/mve_skeleton/`(mock_llm / mas_core / security_oracles / mutators / fuzzer / run.py)。

## 5. 上手顺序(start here)
1. 进 `direction_5/mve_skeleton/`,把 `MockLLM` 换成真客户端:API 走 OpenRouter(`OPENROUTER_API_KEY_2`,proxy `127.0.0.1:7890`,planner `deepseek/deepseek-chat`,judge `openai/gpt-4o-mini`);本地走 HF。先在**1 个 app**上把"mutate→跑 MAS→oracle→report"闭环跑通。
2. 把 4 个 mutation 算子{语义劫持叙事变异 / 工具输出投毒 / observation 注入 / inter-agent message 协议变异}和安全 oracle bank{goal hijack / Grade≥2 越权 / cascading hallucination}接到真 agent trace 上。
3. 接入真实 MAS app(FLARE 那套或 fallback)。
4. 把 **FLARE + AgentFuzzer** 作为 baseline,做 head-to-head:failure-type 覆盖、**PASS→security-fail 计数(M)**、**仅 inter-agent failure 计数(K)**。
5. ≥3 seed,oracle 与人工标注 κ(沿用母论文 κ≥0.87 方法)。

## 6. 成本/吞吐
API 驱动:每个 fuzz trial ≈ 几个 agent turn + 一次 oracle judge ≈ 数次 API 调用。用 DeepSeek-V3 + 4o-mini(便宜)。一次完整 MVE 估 **$50–200**(随 #app × #mutation × #seed)。GPU 路径几乎零 API 成本但要本地推理时间。

## 7. 起跑前必确认(pre-flight)
- [ ] OpenRouter key 可用、proxy 127.0.0.1:7890 通。
- [ ] FLARE 代码+16 app 是否公开(否则启用 fallback app 集)。
- [ ] AgentFuzzer 代码是否公开。
- [ ] gated benchmark 在手。
- [ ] (本地路径)HF token + cache 目录就绪。
- [ ] 定 v1 形态:**API-only 黑盒核心(0 GPU)** vs **含本地 Worker(1×4090)**。

## 8. 一句话给你
**想最快开跑 → 选"最小档",0 显卡,直接拿 OpenRouter 把骨架的 mock 换掉。** 想要可复现 + 为 D1 融合留路 →
**借你一台 AutoDL 4090(24GB)**,下 `Llama-3.1-8B-Instruct` + `bge-small-en-v1.5` 两个即可起步。**R1 永远走 API。**
