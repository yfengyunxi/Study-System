<template>
  <div class="folder-list section-gap">
    <button type="button" :class="['folder-row', selected === null ? 'active' : '']" @click="$emit('select', null)">
      <span>全部资料</span>
      <el-tag size="small">{{ totalCount }}</el-tag>
    </button>
    <button type="button" :class="['folder-row', selected === 'uncategorized' ? 'active' : '']" @click="$emit('select', 'uncategorized')">
      <span>未分类</span>
      <el-tag size="small" type="info">{{ uncategorizedCount }}</el-tag>
    </button>
    <div v-for="folder in folders" :key="folder.id" :class="['folder-row', selected === folder.id ? 'active' : '']">
      <button type="button" class="folder-row-main" @click="$emit('select', folder.id)">
        <strong>{{ folder.name }}</strong>
        <span class="folder-counts">{{ folder.material_count || 0 }} 份 · 可问答 {{ folder.ready_count || 0 }}</span>
      </button>
      <el-dropdown trigger="click" @command="(command) => $emit(command, folder)">
        <el-button text aria-label="文件夹更多操作">⋯</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="edit">重命名</el-dropdown-item>
            <el-dropdown-item command="delete">删除</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
defineProps({
  folders: { type: Array, default: () => [] },
  selected: { type: [Number, String, null], default: null },
  totalCount: { type: Number, default: 0 },
  uncategorizedCount: { type: Number, default: 0 }
})
defineEmits(['select', 'edit', 'delete'])
</script>
