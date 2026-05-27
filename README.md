# 地球动态报告

> EcoPulse-Ocean：基于多模态大模型的海洋碳汇数字孪生与智能审计系统

## 项目愿景

传统的海洋观测数据（ARGO 浮标、卫星遥感、原位传感器）长期存在于科研数据库中，形成"数据孤岛"。大众和跨界决策者无法直观感知海洋生态的真实健康状况。

本项目构建"从微弱电流到地球呼吸"的对齐系统 — 接入全球开源海洋数据，利用 LLM 作为多模态数据分析器，将物理流体、化学泵送指标转化为可交互的 3D 视觉脉搏与自动生成的地球健康报告。

## 系统架构

```
[开源数据源: 卫星遥感 / ARGO / RLC 传感器]
       │
       ▼
[数据预处理与特征提取 (降噪 / 流体力学关联)]
       │
       ▼
[多模态大模型 (LLM Analyst): 语义对齐与逻辑推理]
       │
         ├──────────────────────────────┐
         ▼                              ▼
[自动化地球健康报告 (Markdown/PDF)]   [动态交互视觉 (WebGL/3D 碳汇流场)]
```

### 模块 A：多源异构数据接入与微信号降噪

- **卫星流体动力学对齐**：接入海洋表面风场、流场及温度遥感数据
- **物理传感器信号处理**：模拟/接入原位海洋观测传感器（RLC 电路阻抗传感器）回传的微弱电流特征，利用 Kalman 滤波等算法进行信号去噪，提取生物泵相关特征值

### 模块 B：多模态大模型审计专家 (LLM Core)

- **高维指标语义化**：通过精准的 Prompt Engineering 让大模型充当"海洋学家"，将数值指标转化为人类可读的诊断
- **跨模态推理**：实时解读流体力学数据与生物泵效率之间的因果关系，自动撰写多语言《全球海洋蓝碳健康评估报告》

### 模块 C：数据具象化交互 (Interactive Vision)

- **数字孪生看板**：利用 WebGL/Three.js 将数据转化为动态可交互的"海洋碳汇流场"
- **感知层增强**：报告包含 AI 生成的图表和预警信息，点击任意海域即可查看该处的固碳效率

## 项目结构

```
earthreport/
├── config.py          # 不可变配置与数据模型 (RegionConfig, SimConfig, OceanMetrics 等)
├── data/
│   ├── simulator.py   # 海洋数据模拟器 — 生成多频段时序仿真数据
│   ├── denoiser.py    # 信号降噪管线 — Kalman 滤波 + RLC 信号模型
│   └── connectors.py  # 数据连接器 — 统一接口 (Simulated / Copernicus / ARGO)
├── analyst/           # LLM 分析引擎 (语义对齐与报告生成)
├── dashboard/         # 3D 可视化看板
└── __init__.py
```

## 安装

```bash
git clone <repo-url>
cd ocean-mirror

# 基础安装
pip install -e .

# 含 LLM 支持
pip install -e ".[llm]"

# 含开发工具
pip install -e ".[dev]"
```

## 快速开始

```python
from earthreport.data.connectors import get_connector
from earthreport.data.denoiser import denoise_pipeline
from earthreport.config import REGIONS

# 获取南海区域模拟数据
connector = get_connector("simulated")
metrics = connector.fetch(REGIONS["scs"])

# 运行降噪管线
result = denoise_pipeline(metrics)
print(f"SNR gain: {result.gain_db:.1f} dB")
```

## 开发

```bash
# 格式化与检查
ruff check src/
mypy src/

# 测试
pytest --cov=src --cov-report=term-missing
```

## License

MIT
