<template>
  <div class="header-container">
    <div class="header-left flex-box">
      <el-icon class="icon" size="20" @click="store.commit(`collapseMenu`)"
        ><Fold
      /></el-icon>
      <ul class="flex-box">
        <li
          v-for="(item, index) in selectMenu"
          :key="item.path"
          :class="{ selected: route.path === item.path }"
          class="tab flex-box"
        >
          <el-icon size="12"><component :is="item.icon" /></el-icon>
          <router-link class="text flex-box" :to="{ path: item.path }">{{
            item.name
          }}</router-link>
          <el-icon class="close" size="12" @click="closeTab(item, index)"
            ><Close
          /></el-icon>
        </li>
      </ul>
    </div>
    <div class="header-right">
      <el-dropdown @command="handleClick">
        <div class="el-dropdown-link flex-box">
          <el-avatar
            :src="userInfo.avatar"
          />
          <p class="user-name">{{userInfo.name}}</p>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="cancel">退出</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";

const store = useStore();
const selectMenu = computed(() => store.state.menu.selectMenu);
const router = useRouter();
const route = useRoute();
// console.log(route)

const userInfo = JSON.parse(localStorage.getItem('pz_userInfo'))
// console.log(userInfo)

const closeTab = (item, index) => {
  store.commit("closeMenu", item);
  if (route.path !== item.path) {
    return;
  }
  const selectMenuData = selectMenu.value;
  if (index === selectMenuData.length) {
    if (!selectMenuData.length) {
      router.push("/");
    } else {
      router.push({
        path: selectMenuData[index - 1].path,
      });
    }
  } else {
    router.push({
      path: selectMenuData[index].path,
    });
  }
};

const handleClick = (command) => {
  if (command === "cancel") {
    localStorage.removeItem("pz_token");
    localStorage.removeItem("pz_userInfo");
    localStorage.removeItem("pz_v3pz");
    window.location.href = window.location.origin;
  }
};
</script>

<style lang="less" scoped>
.flex-box {
  display: flex;
  align-items: center;
  height: 100%;
}
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  background-color: #fff;
  padding-right: 25px;
  .header-left {
    height: 100%;
    .icon {
      width: 45px;
      height: 100%;
    }
    .icon:hover {
      cursor: pointer;
      background-color: #f5f5f5;
    }
    .tab {
      padding: 0 10px;
      height: 100px;
      .text {
        margin: 0 5px;
      }
      .close {
        visibility: hidden;
      }
      &.selected {
        a {
          color: #409eff;
        }
        i {
          color: #409eff;
        }
        background-color: #f5f5f5;
      }
    }
    .tab:hover {
      background-color: #f5f5f5;
      .close {
        visibility: inherit;
        cursor: pointer;
        color: #000;
      }
    }
  }
  .header-right {
    .user-name {
      margin-left: 10px;
    }
  }
}

.example-showcase {
  cursor: pointer;
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
}

a {
  height: 100%;
  color: #333;
  font-size: 15pxs;
}
</style>