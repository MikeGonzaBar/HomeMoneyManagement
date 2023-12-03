<template>
  <div class="component-container">

    <div v-if="Object.keys(userData).length == 0" class="centered-container">
      <LoginRegister @userDataSent="handleUserData" @forceRemount="forceRemount" />
    </div>


    <MainPage v-else :userData="userData" />

  </div>
</template>

<script lang="ts">
import LoginRegister from '@/components/LoginRegister.vue'
import MainPage from '@/components/MainPage.vue'
interface UserData {
  first_name: string,
  id: number,
  last_name: string,
  password: string,
  status: string,
  username: string,
}
interface User {
  user: UserData
}

export default {
  name: 'App',
  components: {
    LoginRegister,
    MainPage
  },
  data() {
    return {
      userData: {} as User,
      componentKey: 0,
    };
  },
  mounted() {
    // Get the value of the money_management_user key from localStorage
    const userDataString = localStorage.getItem('money_management_user');
    if (userDataString !== null) {
      this.userData.user = JSON.parse(userDataString);
    } else {
      console.log("money_management_user key not found in local storage");
    }
  },
  methods: {
    forceRemount() {
      this.componentKey++;
    },
    handleUserData(variable: UserData) {
      this.userData.user = variable;
    }
  }

}
</script>

<style scoped>
.component-container {
  background-color: #5870cb;
  width: 100%;
  /* Ensure the component spans the full width */
  min-height: 100vh;
  /* Ensure the component spans the full height of the viewport */

}

.centered-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
}
</style>