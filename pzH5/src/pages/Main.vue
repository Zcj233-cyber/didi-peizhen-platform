<template>
  <div>
    <RouterView />
    <van-tabbar v-model="active">
      <van-tabbar-item
        v-for="item in router.options.routes[0].children"
        :key="item.path"
        :icon="item.meta.icon"
        :url="`#/${item.path}`"
        >{{ item.meta.name }}</van-tabbar-item
      >
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();

const active = ref(0);

onMounted(() => {
  // console.log(router);
  const data = router.options.routes[0];
  active.value = data.children.findIndex(
    (item) => "/" + item.path === route.path
  );
});
</script>

<style>
</style>