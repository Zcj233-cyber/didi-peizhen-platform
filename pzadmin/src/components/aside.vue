<template>
  <el-menu
    :style="{ width: !isCollapse ? '230px' : '64px'}"
    active-text-color="#ffd04b"
    :collapse="isCollapse"
    background-color="#545c64"
    class="aside-contenter"
    text-color="#fff"
    @open="handleOpen"
    @close="handleClose"
    :default-active="active"
  >
    <p class="logo-lg">{{ isCollapse ? "DIDI" : "DIDI陪诊"}}</p>
    <TreeMenu :index="1" :menuData="menuDate" />
  </el-menu>
</template>

<script setup>
import {
  Document,
  Menu as IconMenu,
  Location,
  Setting,
} from "@element-plus/icons-vue";
import TreeMenu from "./treeMenu.vue";
import { useRouter } from "vue-router";
import { ref, reactive, computed } from "vue";
import { useStore } from "vuex";

const router = useRouter();
const store = useStore();
// const menuDate = reactive(router.options.routes[0].children);
const menuDate = computed(() => store.state.menu.routerList);
// console.log(router);
const isCollapse = computed(() => store.state.menu.isCollapse);

const active = computed(() => store.state.menu.menuActive);

const handleOpen = () => {
  // console.log(key, keyPath);
};
const handleClose = () => {
  // console.log(key, keyPath);
};
</script>

<style lang="less" scoped>
.aside-contenter {
  height: 100%;
  .logo-lg {
    font-size: 20px;
    text-align: center;
    height: 50px;
    line-height: 50px;
    color: #fff;
  }
}
</style>