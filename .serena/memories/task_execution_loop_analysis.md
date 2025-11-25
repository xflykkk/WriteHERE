# 任务执行循环问题分析

## 问题描述
用户报告任务执行"到这里又开始循环了,最后的一直没法完成"

## 根本原因分析

### 1. 执行步数限制
- 引擎在`forward_one_step_untill_done`中最多执行10000步
- 超过3000步会记录警告:"Step > 3000, break"
- 如果超过限制,会返回"Out of Step"而不是完成的结果

### 2. 可能导致循环的原因

#### 2.1 规划agent失败
在`UpdateAtomPlanningAgent`中:
- atom判断最多重试10次,如果失败可能导致不确定行为
- 规划生成最多重试10次,失败后可能生成空计划
- 代码位置:`recursive/agent/agents/regular.py:133-259`

#### 2.2 状态转换卡住
状态机流程:`NOT_READY → READY → PLAN_DONE → DOING → FINAL_TO_FINISH → NEED_POST_REFLECT → FINISH`

可能卡住的地方:
- **DOING状态**: 如果内部节点无法到达FINISH,父节点会一直停在DOING
- **检查条件**: `all([inner_node.status == TaskStatus.FINISH for inner_node in node.topological_task_queue])`
- 代码位置:`recursive/graph.py:612-615`

#### 2.3 空计划或无效计划
当`plan2graph`接收空计划时:
```python
if len(raw_plan) == 0:  # 原子任务
    raw_plan.append({
        "id": 0,
        "dependency": [],
        "atom": True,
    })
```
但如果计划格式不正确或缺少必要字段,可能导致节点无法正常执行。

### 3. Reflection机制
所有reflection agent都是Dummy实现:
- `DummyRandomPriorReflectionAgent`: 返回None
- `DummyRandomPlanningPostReflectionAgent`: 返回None  
- `DummyRandomExecutorPostReflectionAgent`: 总是返回status="success"

这意味着reflection不会阻止执行,不是循环的直接原因。

## 解决方案建议

### 短期方案:调试和监控

1. **启用详细日志**
```bash
# 查看引擎日志,定位卡在哪个节点
cat logs/temp/*/engine.log | grep "Do Action"
cat logs/temp/*/engine.log | grep "Step"
```

2. **检查节点状态**
```python
# 在forward_one_step_not_parallel中添加调试输出
logger.info(f"Current nodes status: {[(n.nid, n.status) for n in self.root_node.topological_task_queue]}")
```

3. **监控重试次数**
在`UpdateAtomPlanningAgent.forward`中,如果retry_cnt到达10,记录错误并抛出异常而不是继续。

### 中期方案:改进错误处理

1. **添加超时检测**
```python
# 在forward_one_step_untill_done中添加单步超时检测
same_node_count = {}
if current_node in same_node_count:
    same_node_count[current_node] += 1
    if same_node_count[current_node] > 100:
        logger.error(f"Node {current_node} stuck, executed >100 times")
        break
```

2. **改进规划失败处理**
```python
# 在UpdateAtomPlanningAgent中,如果重试10次后仍失败,抛出异常
if not succ and retry_cnt >= 10:
    raise Exception(f"Planning failed after {retry_cnt} retries for node {node}")
```

3. **添加节点状态检查**
```python
# 在forward_exam中添加卡住检测
if node.status == TaskStatus.DOING:
    stuck_nodes = [n for n in node.topological_task_queue if n.status not in (TaskStatus.FINISH, TaskStatus.FAILED)]
    if len(stuck_nodes) > 0:
        logger.warning(f"Node {node.nid} stuck with {len(stuck_nodes)} incomplete children")
```

### 长期方案:架构改进

1. **实现真正的Reflection机制**
- 验证计划的合理性
- 检查依赖关系是否有效
- 验证执行结果的质量

2. **添加循环依赖检测**
- 在plan2graph后验证拓扑排序是否成功
- 检测并报告循环依赖

3. **改进任务分解策略**
- 限制最大递归深度
- 添加任务复杂度估计
- 自适应调整分解策略

## 立即行动建议

1. 查看最近的执行日志,确定具体卡在哪一步
2. 检查是否有特定类型的任务总是失败
3. 考虑降低任务复杂度或增加步数限制
4. 添加更详细的日志输出以便调试
