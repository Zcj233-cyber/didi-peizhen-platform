<template>
  <el-row class="logon-container" justify="center" :align="`middle`">
    <el-card>
      <template #header>
        <div class="card-header">
          <img :src="imgUrl" alt="" />
        </div>
      </template>

      <div class="jump-link">
        <el-link href="" type="primary" @click="handleChange">{{
          formType ? "返回登录" : "立即注册"
        }}</el-link>
      </div>

      <el-form
        ref="loginFromref"
        :model="loginForm"
        style="max-width: 600px"
        class="demo-ruleForm"
        :rules="rules"
      >
        <el-form-item prop="userName">
          <el-input
            v-model="loginForm.userName"
            placeholder="账号"
            :prefix-icon="UserFilled"
          ></el-input>
        </el-form-item>

        <el-form-item prop="passWord">
          <el-input
            v-model="loginForm.passWord"
            placeholder="密码"
            :prefix-icon="Lock"
            type="password"
          ></el-input>
        </el-form-item>

        <el-form-item v-if="formType" prop="validCode">
          <el-input
            v-model="loginForm.validCode"
            placeholder="验证码"
            :prefix-icon="Lock"
          >
            <template #append>
              <span @click="countdownChange">{{ countdown.validText }}</span>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :style="{ width: '100%' }"
            @click="submitForm(loginFromref)"
            >{{ formType ? "注册" : "登录" }}</el-button
          >
        </el-form-item>
      </el-form>
    </el-card>
  </el-row>
</template>

<script setup>
import { ref, reactive, computed, toRaw } from "vue";
import { getCode, userAuthentication, login, menuPermissions } from "../../api";
import { UserFilled, Lock } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { useStore } from "vuex";

const imgUrl = new URL("../../../public/login-head.png", import.meta.url).href;
const store = useStore();
const router = useRouter();

// const routerList = computed(() => {store.state.menu.routerList})
const routerList = computed(() => store.state.menu.routerList);

const loginForm = reactive({
  userName: "",
  passWord: "",
  validCode: "",
});
// 0:登录 1:注册
const formType = ref(0);
const handleChange = () => {
  formType.value = formType.value ? 0 : 1;
  // console.log(formType.value);
};

const validateUser = (rule, value, callback) => {
  if (value === "") {
    callback(new Error("请输入账号"));
  } else {
    const phoneReg =
      /^1(3[0-9]|4[01456879]|5[0-35-9]|6[2567]|7[0-8]|8[0-9]|9[0-35-9])\d{8}$/;
    phoneReg.test(value)
      ? callback()
      : callback(new Error("手机号格式不正确,请重新输入"));
  }
};

const validatePass = (rule, value, callback) => {
  if (value === "") {
    callback(new Error("请输入密码"));
  } else {
    const reg = /^[a-zA-Z0-9_-]{4,16}$/;
    reg.test(value)
      ? callback()
      : callback(new Error("密码格式不正确,请重新输入"));
  }
};
const rules = reactive({
  userName: [
    {
      validator: validateUser,
      trigger: "blur",
    },
  ],
  passWord: [
    {
      validator: validatePass,
      // message:"请输入密码",
      trigger: "blur",
    },
  ],
  validCode: [
    {
      required: true,
      // message:"请输入验证码",
      trigger: "blur",
    },
  ],
});

const countdown = reactive({
  validText: "获取验证码",
  time: 60,
});
let flag = false;
const countdownChange = () => {
  if (flag) return;
  const phoneReg =
    /^1(3[0-9]|4[01456879]|5[0-35-9]|6[2567]|7[0-8]|8[0-9]|9[0-35-9])\d{8}$/;
  if (!loginForm.userName || !phoneReg.test(loginForm.userName)) {
    return ElMessage({
      message: "请输入正确的手机号",
      type: "error",
    });
  }
  const time = setInterval(() => {
    countdown.time--;
    countdown.validText = `剩余${countdown.time}秒`;
    if (countdown.time <= 0) {
      countdown.validText = "获取验证码";
      countdown.time = 60;
      flag = false;
      clearInterval(time);
    } else {
      countdown.time--;
      countdown.validText = `剩余${countdown.time}秒`;
    }
  }, 1000);
  flag = true;
  getCode({ tel: loginForm.userName }).then(({ data }) => {
    // console.log(data);
    if (data.code === 10000) {
      ElMessage.success("验证码发送成功");
    }
  });
};

const loginFromref = ref();

const submitForm = async (formEl) => {
  if (!formEl) return;
  await formEl.validate((valid, fields) => {
    if (valid) {
      // console.log("submit!");
      if (formType.value) {
        userAuthentication(loginForm).then(({ data }) => {
          if (data.code === 10000) {
            ElMessage.success("注册成功,请登录");
            loginForm.userName = "";
            loginForm.passWord = "";
            loginForm.code = "";
            formType.value = 0;
          }
        });
      } else {
        login(loginForm).then(({ data }) => {
          if (data.code === 10000) {
            ElMessage.success("登录成功");
            localStorage.setItem("pz_token", data.data.token);
            localStorage.setItem(
              "pz_userInfo",
              JSON.stringify(data.data.userInfo || { name: '' }),
            );
            loginForm.userName = "";
            loginForm.passWord = "";
            loginForm.code = "";
            menuPermissions().then((res) => {
              const permData = res.data;
              if (permData.code !== 10000) {
                ElMessage.error(permData.message || "获取菜单权限失败");
                return;
              }
              store.commit("dynamicMenu", permData.data);
              const list = toRaw(store.state.menu.routerList);
              if (list && list.length) {
                list.forEach((item) => {
                  try { router.addRoute("main", item); } catch(e) {}
                });
              }
              // 手动写入 localStorage 确保持久化
              const state = store.state;
              localStorage.setItem("pz_v3pz", JSON.stringify(state));
              setTimeout(() => router.push("/"), 100);
            });
          }
        });
      }
    } else {
      console.log("error submit!", fields);
    }
  });
};
</script>

<style lang="less">
:deep(.el-card__header) {
  padding: 0;
}

.logon-container {
  height: 100%;
  .card-header {
    background-color: #899fe1;
    img {
      width: 430px;
    }
  }
  .jump-link {
    text-align: right;
    margin-bottom: 10px;
  }
}
</style>
