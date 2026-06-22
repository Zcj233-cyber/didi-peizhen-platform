<template>
  <template v-for="(item,index) in props.menuData">
    <el-menu-item
      v-if="!item.children || item.children.length == 0"
      :index="`${props.index}-${item.meta.id}`"
      :key="`${props.index}-${item.meta.id}`"
      @click="handleClick(item, `${props.index}-${item.meta.id}`)"
    >
      <!-- <el-icon><setting /></el-icon> -->
      <!-- <span>{Navigator Four}</span> -->
      <el-icon size="20">
        <component :is="item.meta.icon"></component>
      </el-icon>
      <span>{{ item.meta.name }}</span>
    </el-menu-item>

    <el-sub-menu v-else :index="`${props.index}-${item.meta.id}`" :key="index">
      <template #title>
        <el-icon size="20">
          <component :is="item.meta.icon"></component>
        </el-icon>
        <span>{{ item.meta.name }}</span>
      </template>
      <tree-menu
        :index="`${props.index}-${item.meta.id}`"
        :menuData="item.children"
      />
    </el-sub-menu>
  </template>
</template>

<script setup>
import { useRouter } from "vue-router";
import { useStore } from "vuex";
const store = useStore();
const props = defineProps(["menuData","index"]);
console.log(props.menuData);
const router = useRouter();

const handleClick = (item, index) => {
  // console.log(item, index);

  store.commit("addMenu", item.meta);
  store.commit("updateMenuActive", index);
  router.push(item.meta.path);
};
</script>

<style lang="scss" scoped></style>