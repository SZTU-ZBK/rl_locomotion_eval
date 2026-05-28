# 形态学评估结果解读

**结果目录：** `eval_suite/results/20260529_003711`  
**运行时间：** 2026-05-29 00:37  
**Checkpoint：** `runs/gait-conditioned-agility/pretrain-v0/train/025417.456545`

---

## 1. 实验配置摘要

| 项目 | 设置 |
|------|------|
| 工况 | baseline（1）+ symmetric（16）+ full_asym（16）= **33 变体** |
| 速度搜索 | 二分，粒度 **0.2 m/s**，范围 [0, 4.0] m/s |
| Episode 长度 | **250 步 / 5 s**（dt=0.02 s） |
| 稳态窗口 | speed：末 2 s（100 步）；stability/yaw：末 3 s（150 步） |
| 偏航指标 | **直线行走** vx=1.5, wz=0（与稳定性共用 rollout） |
| 策略 | 预训练 JIT，**未针对变体 URDF 微调** |
| 域随机化 | 全部关闭，仅 URDF 几何变化 |

> 本 run 为 **5 s episode + 直线偏航指标** 的正式版本，可与旧 run `20260529_000839`（60 步 + wz 跟踪）对照趋势，但**绝对数值不可直接对比**。

---

## 2. 三工况汇总对比

| 工况 | v_max (m/s) | yaw 偏移均值 (rad) | yaw 方差均值 (rad²) | base 方差 | 功率 (W) | CoT |
|------|-------------|--------------------|---------------------|-----------|----------|-----|
| **baseline** | **3.75** | **0.018** | 5.92 | **0.0019** | **126** | **1.65** |
| symmetric | 1.20 ± 0.71 | 0.46 ± 0.64 | 3.59 ± 3.22 | 0.73 ± 0.74 | 182 ± 73 | 93 ± 91 |
| full_asym | 1.03 ± 0.62 | 0.39 ± 0.43 | 4.62 ± 3.30 | 0.36 ± 0.50 | 185 ± 65 | 110 ± 182 |

（symmetric / full_asym 为 16 变体均值 ± 标准差）

### 核心结论（一句话）

**标准 Go1 上策略速度可达 ~3.75 m/s、直线偏航偏移仅 ~1°；换用随机 URDF 后速度降至 ~1 m/s 量级、偏航偏移放大 20–30 倍，稳定性方差放大数百倍；symmetric 在极限速度上略优于 full_asym，但 full_asym 的 base 方差反而更低。**

---

## 3. 分项解读

### 3.1 最大速度 v_max（鲁棒性）

- **baseline：** v_max = **3.75 m/s**（success rate 80%，4.0 m/s 失败）。相比旧 run（60 步）的 1.875 m/s **几乎翻倍**——主要因为 5 s episode 给了更长稳态窗口，速度跟踪判定更宽松/更稳定，**不代表策略本身变快**。
- **symmetric 均值 1.20 m/s**，约为 baseline 的 **32%**；中位数 1.25 m/s，离散度大（0–2.25 m/s）。
- **full_asym 均值 1.03 m/s**，略低于 symmetric；**无任何变体 v_max ≥ 2.0 m/s**（symmetric 有 4 个）。

**失效样本：**

| 变体 | scale | symmetric v_max | full_asym v_max | 说明 |
|------|-------|-----------------|-----------------|------|
| v006 | 0.939 | 0.0 | 0.0 | 两工况均无法前进 |
| v009 | 1.045 | 0.0 | 0.0 | 两工况均无法前进 |
| v004 | 0.910 | 0.125 | 1.0 | symmetric 几乎失效 |

另有 symmetric 3 个、full_asym 4 个变体 v_max < 0.5 m/s。

**表现较好的变体（两工况均 v_max ≥ 1.5 m/s）：**

| variant | scale | sym v_max | asym v_max | yaw_off (sym/asym) |
|---------|-------|-----------|------------|-------------------|
| v008 | 0.927 | 2.00 | 1.88 | 0.106 / **0.057** |
| v012 | 0.866 | 2.00 | 1.75 | **0.068** / 0.151 |
| v013 | 0.861 | 2.00 | 1.88 | 0.111 / 0.121 |
| v015 | 0.908 | **2.25** | 1.62 | 0.135 / 0.067 |
| v001 | 0.866 | 1.62 | 1.50 | 0.103 / 0.093 |

**配对对比（同 variant_index）：** symmetric 在 v_max 上赢 11 次，full_asym 赢 2 次，平 3 次。

**scale 相关性：** symmetric 中 scale 与 v_max 呈 **负相关（r ≈ -0.54）**——略大的 scale（接近 1.05）更容易速度崩溃，但非单调，仍取决于具体几何。

---

### 3.2 直线偏航 yaw_offset_mean / yaw_variance（准确程度）

测试条件：vx=1.5 m/s，wz=0，测的是**走直线时的航向漂移**，不是转向跟踪。

| 工况 | yaw_offset_mean | 约合角度 | 相对 baseline |
|------|-----------------|----------|---------------|
| baseline | 0.018 rad | ~1.0° | 1× |
| symmetric | 0.465 rad | ~26.6° | **~26×** |
| full_asym | 0.394 rad | ~22.6° | **~22×** |

**解读：**

- baseline 几乎沿直线走（平均偏离参考航向 1°）。
- 变体 URDF 上机器人**严重偏航**：均值 20–30°，部分样本接近或超过 90°（如 symmetric v006 偏移 2.07 rad ≈ 119°，且 v_max=0）。
- full_asym 的偏航偏移**略好于** symmetric（0.39 vs 0.46 rad），与旧 run 中「非对称更差于对称」的转向跟踪结论**不完全一致**——说明**直线漂移 vs 主动转向跟踪**受 morphology 影响的方式不同。

**偏航 outlier（offset > 1.0 rad）：**

| 工况 | variant | yaw_off | v_max | base_var |
|------|---------|---------|-------|----------|
| symmetric | v005 | 1.82 | 1.25 | 1.84 |
| symmetric | v006 | 2.07 | 0.0 | 1.37 |
| symmetric | v014 | 1.37 | 0.62 | 0.31 |
| full_asym | v000 | 1.17 | 1.25 | 1.38 |
| full_asym | v003 | 1.11 | 1.00 | 0.24 |
| full_asym | v014 | 1.41 | 1.00 | 1.61 |

**最佳直线行走（yaw_off < 0.12 rad 且 v_max ≥ 1.5）：** v008、v012、v001 在两种工况下均表现突出。

**关于 yaw_variance：** 该指标是稳态段**绝对航向角**的方差 Var(yaw)，不是漂移方差。baseline 虽偏移极小，但 yaw_variance=5.92 rad² 仍偏高——可能因为 5 s 内绝对 yaw 缓慢变化或 ±π 包装效应。**解读时以 yaw_offset_mean 为主，yaw_variance 作辅助。**

---

### 3.3 Base 方差 base_variance_scalar（稳定性）

稳态段 var(vx, vy, roll, pitch) 的等权均值（末 3 s）。

| 工况 | 均值 | 相对 baseline |
|------|------|---------------|
| baseline | 0.0019 | 1× |
| symmetric | 0.734 | **~386×** |
| full_asym | 0.363 | **~191×** |

**解读：**

- 变体上速度/姿态波动相对 baseline 放大 **2–3 个数量级**。
- 与旧 run 不同：本次 **full_asym（0.36）优于 symmetric（0.73）**，中位数也更低（0.12 vs 0.25）。可能原因：5 s 长 episode 下 symmetric 部分变体进入持续振荡 whereas full_asym 更快失稳退出或呈现不同失稳模式——需结合 NPZ 时序确认。
- symmetric 有 **7/16** 变体 base_var > 0.5；full_asym 仅 **3/16**。

**高 base_var outlier（> 1.0，roll 方差主导）：**

| 工况 | variant | base_var | var_roll |
|------|---------|----------|----------|
| symmetric | v000 | 1.31 | 4.42 |
| symmetric | v005 | 1.84 | 7.00 |
| symmetric | v011 | 1.89 | 7.41 |
| symmetric | v015 | 1.88 | 7.45 |
| full_asym | v000 | 1.38 | 4.18 |
| full_asym | v010 | 1.17 | 3.63 |
| full_asym | v014 | 1.61 | 6.08 |

---

### 3.4 输出功率 mean_power & CoT（能量效率）

| 工况 | mean_power (W) | 相对 baseline | CoT（中位数） |
|------|----------------|---------------|---------------|
| baseline | 126 | — | 1.65 |
| symmetric | 182 | +45% | 54 |
| full_asym | 185 | +47% | 50 |

**解读：**

- 变体上维持运动平均多消耗 **~45–50%** 功率，符合 morphology 不匹配时的补偿性力矩预期。
- **CoT 在变体上仍不可比**（中位数 ~50，最大可达 788）：低速或失稳时 v_x 过小导致 CoT 爆炸。**报告以 mean_power 为主。**

---

## 4. symmetric vs full_asym 对照

| 维度 | symmetric | full_asym | 谁更差 |
|------|-----------|-----------|--------|
| v_max 均值 | 1.20 | 1.03 | symmetric 更好 |
| v_max ≥ 2.0 的变体数 | 4 | 0 | symmetric |
| yaw 偏移 | 0.46 | 0.39 | full_asym 略好 |
| base 方差 | 0.73 | 0.36 | **full_asym 更好** |
| 功率 | 182 | 185 | 接近 |
| 完全失效 (v_max=0) | 2 | 2 | 相同（v006, v009） |

**结论：** 非对称缩放**一致性地压低极限速度**（配对 win 11:2），但在本次 5 s 设定下**直线稳定性反而略好于等比例缩放**。不能简单认为「full_asym 全面更差」——速度鲁棒性与姿态稳定性受 morphology 影响的路径不同。

---

## 5. 与旧 run（20260529_000839）的趋势对照

| 指标 | 旧 run（60 步, wz 跟踪） | 新 run（5 s, 直线偏航） | 趋势是否一致 |
|------|--------------------------|-------------------------|--------------|
| baseline v_max | 1.88 | 3.75 | 数值不可比（episode 长度效应） |
| symmetric v_max 均值 | 1.20 | 1.20 | ✅ 几乎相同 |
| full_asym v_max 均值 | 1.09 | 1.03 | ✅ 同样偏低 |
| morphology 退化 | 大幅 | 大幅 | ✅ 一致 |
| full_asym vs symmetric | full_asym 全面更差 | 速度 symmetric 更好，稳定性 full_asym 更好 | ⚠️ 部分反转 |

**关键 takeaway：** 延长 episode 后，**变体上的相对退化幅度不变**，说明 60 步旧 run 的趋势判断基本可靠；baseline 绝对 v_max 升高是评估协议变化，不是策略性能突变。

---

## 6. 结果可信度 & 局限

1. **单 checkpoint、零样本迁移：** 策略仅在标准 Go1 URDF 上训练；变体上大幅退化符合预期。
2. **样本量 16/工况：** 足够看趋势，统计显著性有限；扩至 64 变体更稳。
3. **v_max 分辨率 0.2 m/s：** 极限速度为台阶值。
4. **yaw_variance 定义：** 绝对航向方差，与 offset 可脱节；后续可考虑改为 Var(Δyaw)。
5. **v006 / v009 双工况失效：** 值得单独查看 NPZ（`episodes/variant_006/`）确认是否摔倒、卡死或原地打转。

---

## 7. 建议后续

| 优先级 | 行动 |
|--------|------|
| 高 | 对 v006/v009 及 yaw outlier（v005/v014）查看 `straight_line.npz` 时序，确认失稳模式 |
| 中 | 扩至 64 变体，或按 scale 分桶统计 v_max / yaw_off |
| 中 | 考虑将 yaw_variance 改为漂移序列方差 Var(yaw_drift)，与 offset 语义一致 |
| 研究 | morphology-aware 训练 / online adaptation 以提升 v008/v012 类「可迁移」变体的覆盖率 |

---

## 8. 文件索引

| 文件 | 内容 |
|------|------|
| `summary_all.csv` / `summary_all.json` | 33 行完整指标 + 全局 aggregate |
| `COMBINED_REPORT.md` | 三工况均值对比表 |
| `baseline/symmetric/full_asym/REPORT.md` | 各工况明细 |
| `*/episodes/variant_XXX/` | speed_limit.json、straight_line.npz、stability.npz、power.npz |

---

*本解读基于 `summary_all.json` 统计，对应 eval_suite 5 s episode + 直线偏航指标协议。*
