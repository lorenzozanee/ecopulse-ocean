"""Prompt templates for LLM-powered ocean health report generation."""

from __future__ import annotations

from earthreport.analyst.carbon import CarbonMetrics


def carbon_efficiency_prompt(region_cn: str, carbon: CarbonMetrics,
                             sst_mean: float, chl_mean: float) -> str:
    return f"""你是海洋学家，正在撰写"地球动态报告"的碳汇效率评估章节。

## 数据
- 海域：{region_cn}
- 海表温度均值：{sst_mean:.1f}°C
- 叶绿素-a 均值：{chl_mean:.3f} mg/m³
- 颗粒有机碳(POC)在100m通量：{carbon.poc_at_100m:.2f} gC/m²
- Martin曲线指数 b：{carbon.martin_b}
- 导出率 e-ratio：{carbon.export_ratio}
- 碳泵效率百分位：{carbon.carbon_pump_efficiency_percentile:.0f}%
- 评级：{carbon.grade}

## 任务
用中文撰写一段150字以内的评估。包括：
1. 当前碳汇效率的定性判断（优异/良好/一般/较差）
2. 与全球海洋的对比
3. 一句生物学/物理机制解释
4. 对碳封存的意义

只输出报告正文，不要标题、不要编号、不要markdown格式。"""


def heatwave_risk_prompt(region_cn: str, sst_mean: float, sst_anomaly: float,
                         climatology_mean: float) -> str:
    return f"""你是海洋气候学家，正在评估海洋热浪(MHW)风险。

## 数据
- 海域：{region_cn}
- 当前海表温度：{sst_mean:.1f}°C
- 气候态均值：{climatology_mean:.1f}°C
- SST距平：+{sst_anomaly:.1f}°C
- MHW阈值：距平 ≥ 1.0°C 持续5天

## 任务
用中文撰写一段120字以内的热浪风险评估。包括：
1. 当前距平是否接近MHW阈值
2. 未来7天触发概率的定性估计（低/中/高）
3. 对海洋生态系统的潜在影响（珊瑚白化、浮游植物群落变化）
4. 建议

只输出报告正文，不要标题、不要编号。"""


def biodiversity_prompt(region_cn: str, chl_mean: float, chl_std: float) -> str:
    return f"""你是海洋生态学家，正在评估浮游植物多样性代理指标。

## 数据
- 海域：{region_cn}
- 叶绿素-a 均值：{chl_mean:.3f} mg/m³
- 叶绿素-a 标准差：{chl_std:.3f} mg/m³
- 变异系数 CV：{chl_std / max(chl_mean, 0.01):.2f}

## 任务
用中文撰写一段120字以内的生物多样性代理评估。包括：
1. 基于Chl-a变异系数的浮游植物多样性定性判断
2. 温跃层和营养盐供给状态推断
3. 是否有藻华风险

只输出报告正文，不要标题、不要编号。"""


def signal_interpret_prompt(snr_before: float, snr_after: float,
                            gain_db: float, signal_pattern: str) -> str:
    return f"""你是海洋传感器工程师，正在解释RLC微电极传感器的信号特征。

## 数据
- 去噪前SNR：{snr_before:.1f} dB
- 去噪后SNR：{snr_after:.1f} dB
- AI降噪增益：+{gain_db:.1f} dB
- 检测到的信号模式：{signal_pattern}

## 任务
用中文撰写一段120字以内的传感器信号解读。包括：
1. 降噪效果评价
2. 检测到的信号模式对应的物理/生物过程（昼夜周期、潮汐、浊度峰值）
3. 信号质量是否足以支持微生物呼吸速率推断

只输出报告正文，不要标题、不要编号。"""
