<template>
  <AppLayout>
    <PageHeader kicker="Study Plan" title="学习计划" subtitle="今日行动 + 计划进度，一眼看全。">
      <template #actions>
        <el-button :icon="Plus" @click="openPlanDialog">新建计划</el-button>
        <el-button type="primary" :icon="CirclePlus" @click="openTaskDialog()">添加任务</el-button>
      </template>
    </PageHeader>

    <div class="grid stats-grid">
      <MetricCard label="进行中" :value="activePlans.length" icon="📋" hint="未完成的计划" />
      <MetricCard label="待完成" :value="todoCount" icon="📝" hint="未完成的任务" />
      <MetricCard label="今日任务" :value="todayCount" icon="🔔" hint="今天截止或已逾期" />
      <MetricCard label="完成率" :value="`${averageProgress}%`" icon="✅" hint="任务整体完成率" />
    </div>

    <div class="grid two-col-equal section-gap">
      <!-- Left: Today -->
      <div class="panel today-panel">
        <h3 class="panel-title">🔴 今日待办 ({{ todayTasks.length }})</h3>
        <div v-if="!todayTasks.length" class="empty-guide" style="padding:20px">
          <p class="muted">今天没有截止任务 🎉</p>
          <el-button size="small" @click="openTaskDialog()">添加任务</el-button>
        </div>
        <div v-else class="today-list">
          <template v-for="group in todayGroups" :key="group.planName">
            <div class="today-group-label">{{ group.planName }}</div>
            <div v-for="task in group.tasks" :key="task.id" :class="['today-task', { overdue: task.is_overdue }]">
              <el-checkbox :model-value="task.status === 'done'" @change="toggleTask(task)" />
              <span class="today-task-title" @click="openEditDialog(task)">{{ task.title }}</span>
              <el-button size="small" @click.stop="toggleTask(task)">完成</el-button>
              <span class="today-task-arrow" @click="openEditDialog(task)">▸</span>
            </div>
          </template>
        </div>
      </div>

      <!-- Right: Active plan overview -->
      <div class="panel overview-panel">
        <h3 class="panel-title">📊 未完成计划总览</h3>
        <div v-if="!activePlans.length" class="empty-guide" style="padding:20px">
          <p class="muted">还没有进行中的计划</p>
          <el-button size="small" @click="openPlanDialog">创建第一个计划</el-button>
        </div>
        <div v-else class="overview-list">
          <div v-for="plan in activePlans" :key="plan.id" class="overview-item">
            <span class="overview-name">{{ plan.title }}</span>
            <el-progress
              :percentage="plan.progress_percent || 0" :stroke-width="8"
              :color="plan.status === 'overdue' ? '#ff7a66' : '#2f80ed'"
              style="flex:1;margin:0 10px"
            />
            <span class="overview-stat">{{ plan.done_count }}/{{ plan.task_count }}</span>
          </div>
        </div>
        <div class="overview-actions">
          <el-button size="small" @click="openPlanDialog">新建计划</el-button>
          <el-button size="small" type="primary" @click="openTaskDialog()">添加任务</el-button>
        </div>
      </div>
    </div>

    <!-- Plan accordion -->
    <div class="panel section-gap">
      <h3 class="panel-title">📂 未完成计划详情</h3>
      <p class="panel-subtitle">点击展开查看任务，☑ 直接标记完成，▸ 编辑详情。</p>
      <div v-if="!activePlans.length && !archivedPlans.length" class="muted" style="padding:16px 0">暂无计划</div>
      <div v-else class="plan-accordion">
        <div v-for="plan in activePlans" :key="plan.id" class="accordion-item" :class="{ open: expandedPlanId === plan.id }">
          <div class="accordion-header" @click="toggleExpand(plan.id)">
            <span class="accordion-arrow">{{ expandedPlanId === plan.id ? '▾' : '▸' }}</span>
            <span class="accordion-title">{{ plan.title }}</span>
            <span v-if="plan.status === 'overdue'" class="accordion-badge overdue">⚠ {{ plan.overdue_count }}逾期</span>
            <span v-else-if="plan.status === 'not_started'" class="accordion-badge future">未开始</span>
            <span class="accordion-stat">{{ plan.done_count }}/{{ plan.task_count }} · {{ plan.progress_percent }}%</span>
          </div>
          <div v-if="expandedPlanId === plan.id" class="accordion-body">
            <p v-if="plan.description" class="accordion-desc">{{ plan.description }}</p>
            <p class="muted" style="font-size:11px;margin:0 0 10px">{{ plan.start_date || '未设' }} — {{ plan.end_date || '未设' }}</p>

            <!-- Two-column task layout -->
            <div class="accordion-task-grid">
              <div class="accordion-task-col">
                <div class="task-section-label">待完成 ({{ planTodoTasks(plan.id).length }})</div>
                <div v-if="!planTodoTasks(plan.id).length" class="muted" style="font-size:11px;padding:8px 0">全部完成 🎉</div>
                <div v-else class="task-section-list">
                  <div
                    v-for="task in planTodoTasks(plan.id)" :key="task.id"
                    :class="['task-row', { urgent: task.is_overdue || task.days_until_due === 0 }]"
                  >
                    <el-checkbox :model-value="false" size="small" @change="toggleTask(task)" @click.stop />
                    <span class="task-text" @click="openEditDialog(task)">{{ task.title }}</span>
                    <span :class="['task-due', { today: task.days_until_due === 0, overdue: task.is_overdue }]">{{ task.due_date || '未设' }}</span>
                    <el-button size="small" @click.stop="toggleTask(task)">完成</el-button>
                    <span class="task-arrow" @click="openEditDialog(task)">▸</span>
                  </div>
                </div>
              </div>

              <div class="accordion-task-col">
                <div class="task-section-label">已完成 ({{ planDoneTasks(plan.id).length }})</div>
                <div v-if="!planDoneTasks(plan.id).length" class="muted" style="font-size:11px;padding:8px 0">暂无</div>
                <div v-else class="task-section-list">
                  <div v-for="task in planDoneTasks(plan.id)" :key="task.id" class="task-row done" @click="openEditDialog(task)">
                    <el-checkbox :model-value="true" size="small" @change="toggleTask(task)" @click.stop />
                    <span class="task-text">{{ task.title }}</span>
                    <span class="task-date">{{ task.completed_at?.slice(0, 10) }}</span>
                    <span class="task-arrow">▸</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="accordion-footer">
              <el-button size="small" @click="openTaskDialog(plan.id)">+ 添加任务</el-button>
              <el-button size="small" type="danger" @click="removePlan(plan)">删除计划</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Completed plans -->
    <div v-if="archivedPlans.length" class="panel section-gap">
      <div class="archive-header" @click="showArchived = !showArchived">
        <span class="archive-arrow">{{ showArchived ? '▾' : '▸' }}</span>
        <h3 class="panel-title" style="margin:0">📦 已完成计划 ({{ archivedPlans.length }})</h3>
        <span class="archive-hint">点击展开</span>
      </div>
      <div v-if="showArchived" class="plan-accordion section-gap">
        <div v-for="plan in archivedPlans" :key="plan.id" class="accordion-item" :class="{ open: expandedPlanId === plan.id }">
          <div class="accordion-header" @click="toggleExpand(plan.id)">
            <span class="accordion-arrow">{{ expandedPlanId === plan.id ? '▾' : '▸' }}</span>
            <span class="accordion-title">{{ plan.title }}</span>
            <span class="accordion-badge done">✓ 完成</span>
            <span class="accordion-stat">{{ plan.done_count }}/{{ plan.task_count }} · 100%</span>
          </div>
          <div v-if="expandedPlanId === plan.id" class="accordion-body">
            <p v-if="plan.description" class="accordion-desc">{{ plan.description }}</p>
            <div v-if="planTasks(plan.id).length" class="task-section-list">
              <div v-for="task in planTasks(plan.id)" :key="task.id" class="task-row done" @click="openEditDialog(task)">
                <el-checkbox :model-value="true" size="small" @change="toggleTask(task)" @click.stop />
                <span class="task-text">{{ task.title }}</span>
                <span class="task-date">{{ task.completed_at?.slice(0, 10) }}</span>
                <span class="task-arrow">▸</span>
              </div>
            </div>
            <div class="accordion-footer">
              <el-button size="small" type="danger" @click="removePlan(plan)">删除计划</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Task edit dialog -->
    <el-dialog v-model="editDialog" title="编辑任务" width="480px" :close-on-click-modal="false">
      <template v-if="editTask">
        <el-form label-position="top">
          <el-form-item label="任务标题">
            <el-input v-model="editTask.title" />
          </el-form-item>
          <el-form-item label="说明">
            <el-input v-model="editTask.description" type="textarea" :rows="3" placeholder="具体完成标准或笔记" />
          </el-form-item>
          <el-form-item label="截止日期">
            <el-date-picker v-model="editTask.due_date" value-format="YYYY-MM-DD" class="full-width" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="editTask.status" class="full-width">
              <el-option label="待完成" value="todo" />
              <el-option label="已完成" value="done" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属计划">
            <el-select v-model="editTask.plan_id" clearable placeholder="不选择计划" class="full-width">
              <el-option v-for="plan in plans" :key="plan.id" :label="plan.title" :value="plan.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button type="danger" @click="deleteTaskFromEdit">删除任务</el-button>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Plan dialog -->
    <el-dialog v-model="planDialog" title="新建计划" width="460px">
      <el-form :model="planForm" label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="planForm.title" placeholder="例如：两周完成数据库复习" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="planForm.description" type="textarea" placeholder="写下计划目标和学习范围" />
        </el-form-item>
        <el-form-item label="周期">
          <el-date-picker v-model="planRange" type="daterange" value-format="YYYY-MM-DD"
            start-placeholder="开始日期" end-placeholder="结束日期" class="full-width" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialog = false">取消</el-button>
        <el-button type="primary" @click="savePlan">保存</el-button>
      </template>
    </el-dialog>

    <!-- Task create dialog -->
    <el-dialog v-model="taskDialog" title="添加任务" width="460px">
      <el-form :model="taskForm" label-position="top">
        <el-form-item label="所属计划">
          <el-select v-model="taskForm.plan_id" clearable placeholder="不选择计划" class="full-width">
            <el-option v-for="plan in plans" :key="plan.id" :label="plan.title" :value="plan.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务标题" required>
          <el-input v-model="taskForm.title" placeholder="例如：整理第 3 章笔记" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="taskForm.description" type="textarea" placeholder="可选" />
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
import { CirclePlus, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { planApi, taskApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import MetricCard from '../components/study/MetricCard.vue'
import PageHeader from '../components/study/PageHeader.vue'

const plans = ref([])
const allTasks = ref([])
const loading = ref(false)
const planDialog = ref(false)
const taskDialog = ref(false)
const editDialog = ref(false)
const planRange = ref([])
const expandedPlanId = ref(null)
const showArchived = ref(false)
const planForm = reactive({ title: '', description: '' })
const taskForm = reactive({ plan_id: null, title: '', description: '', due_date: '' })
const editTask = ref(null)

const activePlans = computed(() => plans.value.filter(p => p.status !== 'completed'))
const archivedPlans = computed(() => plans.value.filter(p => p.status === 'completed'))

const todoCount = computed(() => allTasks.value.filter(t => t.status !== 'done').length)
const todayCount = computed(() => allTasks.value.filter(t => t.status !== 'done' && (t.days_until_due === 0 || t.is_overdue)).length)
const averageProgress = computed(() => {
  if (!allTasks.value.length) return 0
  return Math.round(allTasks.value.filter(t => t.status === 'done').length / allTasks.value.length * 100)
})

const todayTasks = computed(() =>
  allTasks.value.filter(t => t.status !== 'done' && (t.days_until_due === 0 || t.is_overdue))
)

const todayGroups = computed(() => {
  const map = new Map()
  for (const t of todayTasks.value) {
    const key = t.plan_title || '独立任务'
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(t)
  }
  return [...map.entries()].map(([planName, tasks]) => ({ planName, tasks }))
})

function planTasks(planId) { return allTasks.value.filter(t => t.plan_id === planId) }
function planDoneTasks(planId) { return planTasks(planId).filter(t => t.status === 'done') }
function planTodoTasks(planId) { return planTasks(planId).filter(t => t.status !== 'done') }

function toggleExpand(planId) {
  expandedPlanId.value = expandedPlanId.value === planId ? null : planId
}

async function load() {
  loading.value = true
  try {
    const [planRows, taskRows] = await Promise.all([planApi.list(), taskApi.list()])
    plans.value = planRows
    allTasks.value = taskRows
  } finally { loading.value = false }
}

function openPlanDialog() {
  planForm.title = ''; planForm.description = ''; planRange.value = []
  planDialog.value = true
}

async function savePlan() {
  if (!planForm.title) { ElMessage.warning('请输入计划标题'); return }
  await planApi.create({
    title: planForm.title, description: planForm.description,
    start_date: planRange.value?.[0], end_date: planRange.value?.[1]
  })
  planDialog.value = false; ElMessage.success('计划已创建'); await load()
}

function openTaskDialog(planId = null) {
  taskForm.plan_id = planId; taskForm.title = ''; taskForm.description = ''; taskForm.due_date = ''
  taskDialog.value = true
}

async function saveTask() {
  if (!taskForm.title) { ElMessage.warning('请输入任务标题'); return }
  await taskApi.create(taskForm)
  taskDialog.value = false; ElMessage.success('任务已创建'); await load()
}

async function toggleTask(task) {
  if (task.status === 'done') await taskApi.undo(task.id)
  else await taskApi.complete(task.id)
  await load()
}

function openEditDialog(task) {
  editTask.value = {
    id: task.id, title: task.title, description: task.description || '',
    due_date: task.due_date || '', status: task.status, plan_id: task.plan_id || null
  }
  editDialog.value = true
}

async function saveEdit() {
  const t = editTask.value
  if (!t || !t.title) { ElMessage.warning('请输入任务标题'); return }
  await taskApi.update(t.id, {
    title: t.title, description: t.description,
    due_date: t.due_date || null, status: t.status, plan_id: t.plan_id
  })
  editDialog.value = false; ElMessage.success('任务已更新'); await load()
}

async function deleteTaskFromEdit() {
  if (!editTask.value) return
  await ElMessageBox.confirm('确认删除该任务？', '删除任务')
  await taskApi.remove(editTask.value.id)
  editDialog.value = false; ElMessage.success('任务已删除'); await load()
}

async function removePlan(plan) {
  await ElMessageBox.confirm('删除计划会同时删除其任务，确认继续？', '删除计划')
  await planApi.remove(plan.id)
  if (expandedPlanId.value === plan.id) expandedPlanId.value = null
  ElMessage.success('计划已删除'); await load()
}

onMounted(load)
</script>
