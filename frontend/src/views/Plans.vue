<template>
  <AppLayout>
    <PageHeader
      kicker="Study Plan"
      title="学习计划"
      subtitle="把大目标拆成每天能完成的小任务，让学习进度更清楚。"
    >
      <template #actions>
        <el-button :icon="Plus" @click="openPlanDialog">新建计划</el-button>
        <el-button type="primary" :icon="CirclePlus" @click="openTaskDialog(selectedPlanId)">添加任务</el-button>
      </template>
    </PageHeader>

    <div class="grid stats-grid">
      <MetricCard label="计划数量" :value="plans.length" icon="划" hint="当前账号下的学习计划" />
      <MetricCard label="待完成任务" :value="todoCount" icon="待" hint="尚未完成的小步骤" />
      <MetricCard label="今日任务" :value="todayCount" icon="今" hint="今天截止或需要优先处理" />
      <MetricCard label="整体进度" :value="`${averageProgress}%`" icon="✓" hint="所有任务的平均完成率" />
    </div>

    <div class="grid two-col section-gap">
      <WorkbenchPanel title="学习计划" subtitle="点击计划卡片可聚焦右侧任务。">
        <template #actions>
          <el-button v-if="selectedPlanId" @click="selectPlan(null)">显示全部</el-button>
        </template>
        <el-empty v-if="!loading && !plans.length" description="还没有学习计划，先创建一个本周目标吧" />
        <div v-else class="plan-card-grid">
          <PlanCard
            v-for="plan in plans"
            :key="plan.id"
            :plan="plan"
            :active="plan.id === selectedPlanId"
            @select="selectPlan($event.id)"
            @add-task="openTaskDialog($event.id)"
            @remove="removePlan($event)"
          />
        </div>
      </WorkbenchPanel>

      <WorkbenchPanel title="任务看板" subtitle="今日、即将到期、未安排和已完成任务。">
        <template #actions>
          <el-select v-model="taskScope" class="task-scope-select" placeholder="任务范围">
            <el-option label="全部任务" value="all" />
            <el-option label="今日" value="today" />
            <el-option label="逾期" value="overdue" />
            <el-option label="即将到期" value="upcoming" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </template>
        <TaskBoard :columns="boardColumns" @complete="completeTask" @undo="undoTask" @remove="removeTask" />
      </WorkbenchPanel>
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
          <p class="panel-subtitle">不选择计划时，该任务仍会按截止日期进入任务看板。</p>
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
import { CirclePlus, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { planApi, taskApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import MetricCard from '../components/study/MetricCard.vue'
import PageHeader from '../components/study/PageHeader.vue'
import PlanCard from '../components/study/PlanCard.vue'
import TaskBoard from '../components/study/TaskBoard.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'

const route = useRoute()
const router = useRouter()
const plans = ref([])
const today = ref([])
const allTasks = ref([])
const loading = ref(false)
const planDialog = ref(false)
const taskDialog = ref(false)
const planRange = ref([])
const selectedPlanId = ref(Number(route.params.id || route.query.plan_id) || null)
const taskScope = ref(String(route.query.task_scope || 'all'))
const planForm = reactive({ title: '', description: '' })
const taskForm = reactive({ plan_id: null, title: '', description: '', due_date: '' })

const todoCount = computed(() => allTasks.value.filter((task) => task.status !== 'done').length)
const todayCount = computed(() => allTasks.value.filter((task) => task.days_until_due === 0 || task.is_overdue).length)
const averageProgress = computed(() => {
  if (!allTasks.value.length) return 0
  const done = allTasks.value.filter((task) => task.status === 'done').length
  return Math.round(done / allTasks.value.length * 100)
})

const visibleTasks = computed(() => {
  let rows = [...allTasks.value]
  if (selectedPlanId.value) rows = rows.filter((task) => task.plan_id === selectedPlanId.value)
  if (taskScope.value === 'today') rows = rows.filter((task) => task.days_until_due === 0 || task.is_overdue)
  if (taskScope.value === 'overdue') rows = rows.filter((task) => task.is_overdue)
  if (taskScope.value === 'upcoming') rows = rows.filter((task) => task.status !== 'done' && task.days_until_due > 0)
  if (taskScope.value === 'completed') rows = rows.filter((task) => task.status === 'done')
  return rows
})

const boardColumns = computed(() => {
  const todayTasks = visibleTasks.value.filter((task) => task.status !== 'done' && task.days_until_due === 0)
  const overdueTasks = visibleTasks.value.filter((task) => task.status !== 'done' && task.is_overdue)
  const upcoming = visibleTasks.value.filter((task) => task.status !== 'done' && task.days_until_due > 0)
  const unscheduled = visibleTasks.value.filter((task) => task.status !== 'done' && !task.due_date)
  const completed = visibleTasks.value.filter((task) => task.status === 'done')
  return [
    { key: 'today', title: '今日', empty: '今天没有截止任务', items: [...overdueTasks, ...todayTasks] },
    { key: 'upcoming', title: '即将到期', empty: '暂无未来任务', items: upcoming },
    { key: 'unscheduled', title: '未安排', empty: '暂无未安排任务', items: unscheduled },
    { key: 'completed', title: '已完成', empty: '暂无已完成任务', items: completed }
  ]
})

watch(taskScope, (value) => {
  router.replace({ query: { ...route.query, task_scope: value === 'all' ? undefined : value } })
})

async function load() {
  loading.value = true
  try {
    const [planRows, taskRows, todayRows] = await Promise.all([
      planApi.list(),
      taskApi.list(),
      taskApi.today()
    ])
    plans.value = planRows
    allTasks.value = taskRows
    today.value = todayRows
    if (selectedPlanId.value && !plans.value.some((plan) => plan.id === selectedPlanId.value)) {
      ElMessage.warning('链接中的学习计划不存在，已显示全部计划')
      selectedPlanId.value = null
      router.replace('/plans')
    }
  } finally {
    loading.value = false
  }
}

function selectPlan(planId) {
  selectedPlanId.value = planId
  if (planId) router.push(`/plans/${planId}`)
  else router.push('/plans')
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
  const plan = await planApi.create({
    title: planForm.title,
    description: planForm.description,
    start_date: planRange.value?.[0],
    end_date: planRange.value?.[1]
  })
  planDialog.value = false
  selectedPlanId.value = plan.id
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

async function completeTask(task) {
  await taskApi.complete(task.id)
  await load()
}

async function undoTask(task) {
  await taskApi.undo(task.id)
  await load()
}

async function removePlan(plan) {
  await ElMessageBox.confirm('删除计划会同时删除其任务，确认继续？', '删除计划')
  await planApi.remove(plan.id)
  if (selectedPlanId.value === plan.id) selectedPlanId.value = null
  ElMessage.success('计划已删除')
  await load()
}

async function removeTask(task) {
  await ElMessageBox.confirm('确认删除该任务？', '删除任务')
  await taskApi.remove(task.id)
  ElMessage.success('任务已删除')
  await load()
}

onMounted(load)
</script>
