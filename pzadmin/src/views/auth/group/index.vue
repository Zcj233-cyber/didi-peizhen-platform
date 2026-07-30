<template>
  <div>
    <panel-head :route="route" />
    <div class="btns">
      <el-button :icon="Plus" type="primary" @click="open(null)">新增</el-button>
    </div>
    <el-table :data="tableData.list" style="width: 100%">
      <el-table-column prop="id" label="id" />
      <el-table-column prop="name" label="昵称" />
      <el-table-column prop="permissionName" label="菜单权限" width="500px" />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="primary" @click="open(scope.row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination-info" style="display:flex;justify-content:space-between;align-items:center;padding:10px">
      <span style="font-size:13px;color:#999">显示第 {{ (paginationData.pageNum-1)*paginationData.pageSize+1 }}-{{ Math.min(paginationData.pageNum*paginationData.pageSize, tableData.total) }} 条，共 {{ tableData.total }} 条</span>
      <el-pagination
        :current-page="paginationData.pageNum"
        :page-size="paginationData.pageSize"
        layout="prev, pager, next"
        :total="tableData.total"
        @size-change="v=>{paginationData.pageSize=v;getListData()}"
        @current-change="v=>{paginationData.pageNum=v;getListData()}"
      />
    </div>
    <el-dialog
      v-model="dialogFormVisable"
      :before-close="beforeClose"
      title="添加权限"
      width="500"
    >
      <el-form
        ref="formRef"
        label-width="100px"
        label-position="left"
        :model="form"
        :rules="rules"
      >
        <el-form-item v-show="false" prop="id">
          <input v-model="form.id" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请填写权限名称"></el-input>
        </el-form-item>
        <el-form-item label="权限" prop="permissions">
          <el-tree
            ref="treeRef"
            style="max-width: 600px"
            :data="permissionData"
            node-key="id"
            show-checkbox
            :default-checked-keys="defaultKeys"
            :default-expanded-keys="[2]"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div>
          <el-button type="primary" @click="confirm(formRef)">确认</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from "vue";
import { userGetMenu, userSetMenu, menuList } from "../../../api";
import { Plus} from "@element-plus/icons-vue";
import {useRoute} from 'vue-router'

const route = useRoute()

const form = reactive({
  name: "",
  permissions: "",
  id: "",
});

const permissionData = ref([]);

onMounted(() => {
  userGetMenu().then(({ data }) => {
    // console.log(data);
    permissionData.value = data.data;
    // console.log(permissionData.value);
    getListData();
  });
});

const tableData = reactive({
  list: [],
  total: 0,
});

const paginationData = reactive({
  pageNum: 1,
  pageSize: 10,
});

const handleSizeChange = (val) => {
  paginationData.pageSize = val;
  getListData();
};

const handleCurrentChange = (val) => {
  paginationData.pageNum = val;
  getListData();
};

const open = (rowData = {}) => {
  dialogFormVisable.value = true;
  nextTick(() => {
    if (rowData) {
      // console.log(rowData);
      Object.assign(form, { id: rowData.id, name: rowData.name });
      treeRef.value.setCheckedKeys(rowData.permission);
    }
  });
};

const getListData = () => {
  menuList(paginationData).then(({ data }) => {
    const { list, total } = data.data;
    tableData.list = list;
    tableData.total = total;
  });
};

const formRef = ref();

const dialogFormVisable = ref(false);
const beforeClose = () => {
  dialogFormVisable.value = false;
  formRef.value.resetFields();
  treeRef.value.setCheckedKeys(defaultKeys);
};

const defaultKeys = [4, 5];
const treeRef = ref();

const rules = {
  name: [
    {
      required: true,
      trigger: "blur",
      message: "请输入权限名称",
    },
  ],
};

const confirm = async (formEl) => {
  if (!formEl) return;
  await formEl.validate((valid, fields) => {
    if (valid) {
      const permissions = JSON.stringify(treeRef.value.getCheckedKeys());
      userSetMenu({ name: form.name, permissions, id: form.id }).then(
        ({ data }) => {
          // console.log(data);
          beforeClose();
          getListData();
        }
      );
    } else {
      console.log("error submit!", fields);
    }
  });
};
</script>

<style lang="less" scoped>
.btns{
  padding: 10px 0 10px 10px;
  background-color: #fff;
}
</style>