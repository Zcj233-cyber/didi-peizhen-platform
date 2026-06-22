<template>
  <div>
    <h1>用户登录</h1>
    <van-form @submit="onSubmit">
      <van-field
        v-model="form.userName"
        name="用户名"
        label="用户名"
        placeholder="用户名"
        :rules="[{ required: true, message: '请填写用户名' }]"
      />
      <van-field
        v-model="form.passWord"
        name="密码"
        label="密码"
        placeholder="密码"
        type="password"
        :rules="[{ required: true, message: '请填写密码' }]"
      />
      <div class="btn">
        <van-button native-type="submit" round block type="primary">提交</van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive,getCurrentInstance } from "vue";
import { useRouter } from "vue-router";

// 获取当前vue实例
const {proxy} = getCurrentInstance();
const router = useRouter();

const form = reactive({
  userName: "",
  passWord: "",
});
const onSubmit = async () => {
  const {data} = await proxy.$api.login(form)
  if(data.code === 10000){
    localStorage.setItem('h5_token',data.data.token)
    localStorage.setItem('h5_userInfo',JSON.stringify(data.data.userInfo))
    router.push('/home')
  }
};
</script>

<style lang="less" scoped>
h1{
  text-align: center;
}
.btn{
  margin: 16px;
}
</style>