<template>
  <AppLayout>
    <div class="page-heading">
      <div>
        <p class="page-kicker">Study Plan</p>
        <h1 class="page-title">学习计划</h1>
        <p class="page-subtitle">把大目标拆成每天能完成的小任务，让学习进度更清楚。</p>
      </div>
      <div class="toolbar-actions">
        <el-button :icon="Plus" @click="openPlanDialog">新建计划</el-button>
        <el-button type="primary" :icon="CirclePlus" @click="openTaskDialog()">添加任务</el-button>
      </div>
    </div>

    <div class="grid two-col">
      <div class="panel">
        <div class="toolbar">
          <div>
            <h3 class="panel-title">计划列表</h3>
            <p class="panel-subtitle">按阶段组织任务，适合课程复习、实验报告和项目推进。</p>
          </div>
        </div>
        <el-empty v-if="!loading && !plans.length" description="还没有学习计划，先创建一个本周目标吧" />
        <div v-else class="table-wrap">
          <el-table :data="plans" v-loading="loading">
            <el-table-column prop="title" label="计划" min-width="160" />
            <el-table-column label="周期" min-width="180">
              <template #default="{ row }">
                {{ row.start_date || '未设' }} - {{ row.end_date || '未设' }}
              </template>
            </el-table-column>
            <el-table-column label="任务" width="90">
              <template #default="{ row }">{{ row.tasks?.length || 0 }}</template>
            </el-table-column>
            <el-table-column label="操作" width="190">
              <template #default="{ row }">
                <el-button :icon="CirclePlus" @click="openTaskDialog(row.id)">任务</el-button>
                <el-button :icon="Delete" type="danger" @click="removePlan(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="panel">
        <h3 class="panel-title">今日任务</h3>
        <p class="panel-subtitle">今天先完成这些小步骤。勾选后会同步更新任务状态。</p>
        <el-empty v-if="!today.length" description="今天还没有任务，可以添加一个轻量目标" />
        <div v-else>
          <div v-for="task in today" :key="task.id" class="task-card">
            <el-checkbox :model-value="task.status === 'done'" @change="toggleTask(task)">
              <strong>{{ task.title }}</strong>
            </el-checkbox>
            <p class="muted">{{ task.description || '暂无说明' }}</p>
            <el-tag :type="task.status === 'done' ? 'success' : 'warning'" size="small">
              {{ task.status === 'done' ? '已完成' : '待完成' }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="panel section-gap">
      <div class="toolbar">
        <div>
          <h3 class="panel-title">计划内任务</h3>
          <p class="panel-subtitle">这里展示已归属到学习计划的任务；未选择计划的任务仍会在“今日任务”中按日期出现。</p>
        </div>
      </div>
      <el-empty v-if="!allTasks.length" description="暂无计划内任务" />
      <div v-else class="table-wrap">
        <el-table :data="allTasks">
          <el-table-column prop="title" label="任务" min-width="180" />
          <el-table-column prop="due_date" label="截止日期" width="140" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'done' ? 'success' : 'info'">
                {{ row.status === 'done' ? '已完成' : '待完成' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button
                :icon="Check"
                :type="row.status === 'done' ? 'info' : 'success'"
                @click="toggleTask(row)"
              >
                {{ row.status === 'done' ? '撤销' : '完成' }}
              </el-button>
              <el-button :icon="Delete" type="danger" @click="removeTask(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="planDialog" title="新建计划" width="460px">
      <el-form :model="planForm" label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="planForm.title" placeholder="例如：两周完成数据库复习" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="planForm.description" type="textarea" placeholder="写下计划目标和学习范围" />
        </el-form-item>
        <el-form-item label="周期">
          <el-date-picker
            v-model="planRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            class="full-width"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialog = false">取消</el-button>
        <el-button type="primary" @click="savePlan">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="taskDialog" title="添加任务" width="460px">
      <el-form :model="taskForm" label-position="top">
        <el-form-item label="所属计划">
          <el-select v-model="taskForm.plan_id" clearable placeholder="不选择计划" class="full-width">
            <el-option v-for="plan in plans" :key="plan.id" :label="plan.title" :value="plan.id" />
          </el-select>
          <p class="panel-subtitle">不选择计划时，该任务不会出现在“计划内任务”表格，但到期日为今天时会出现在“今日任务”。</p>
        </el-form-item>
        <el-form-item label="任务标题" required>
          <el-input v-model="taskForm.title" placeholder="例如：整理第 3 章笔记" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="taskForm.description" type="textarea" placeholder="可选，写下具体完成标准" />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="taskForm.due_date" value-format="YYYY-MM-DD" class="full-width" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>
  </AppLayout>
</template>

<script setup>
import { Check, CirclePlus, Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { planApi, taskApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'

const plans = ref([])
const today = ref([])
const loading = ref(false)
const planDialog = ref(false)
const taskDialog = ref(false)
const planRange = ref([])
const planForm = reactive({ title: '', description: '' })
const taskForm = reactive({ plan_id: null, title: '', description: '', due_date: '' })

const allTasks = computed(() => plans.value.flatMap((plan) => plan.tasks || []))

async function load() {
  loading.value = true
  try {
    plans.value = await planApi.list()
    today.value = await taskApi.today()
  } finally {
    loading.value = false
  }
}

function openPlanDialog() {
  planForm.title = ''
  planForm.description = ''
  planRange.value = []
  planDialog.value = true
}

async function savePlan() {
  if (!planForm.title) {
    ElMessage.warning('请输入计划标题')
    return
  }
  await planApi.create({
    title: planForm.title,
    description: planForm.description,
    start_date: planRange.value?.[0],
    end_date: planRange.value?.[1]
  })
  planDialog.value = false
  ElMessage.success('计划已创建')
  await load()
}

function openTaskDialog(planId = null) {
  taskForm.plan_id = planId
  taskForm.title = ''
  taskForm.description = ''
  taskForm.due_date = ''
  taskDialog.value = true
}

async function saveTask() {
  if (!taskForm.title) {
    ElMessage.warning('请输入任务标题')
    return
  }
  await taskApi.create(taskForm)
  taskDialog.value = false
  ElMessage.success('任务已创建')
  await load()
}

async function toggleTask(task) {
  if (task.status === 'done') {
    await taskApi.undo(task.id)
  } else {
    await taskApi.complete(task.id)
  }
  await load()
}

async function removePlan(id) {
  await ElMessageBox.confirm('删除计划会同时删除其任务，确认继续？', '删除计划')
  await planApi.remove(id)
  ElMessage.success('计划已删除')
  await load()
}

async function removeTask(id) {
  await ElMessageBox.confirm('确认删除该任务？', '删除任务')
  await taskApi.remove(id)
  ElMessage.success('任务已删除')
  await load()
}

onMounted(load)
</script>
