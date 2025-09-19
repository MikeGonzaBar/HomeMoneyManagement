<template>
  <div class="component-container">

    <div v-if="Object.keys((this as any).userData).length == 0" class="centered-container">
      <LoginRegister @userDataSent="(this as any).handleUserData" @forceRemount="(this as any).forceRemount" />
    </div>


    <MainPage v-else :userData="(this as any).userData" />

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
      const parsedUserData = JSON.parse(userDataString);

      // Fix: The localStorage data has structure {user: {...}, valid: true}
      // We need to extract the inner user object
      if (parsedUserData.user) {
        (this as any).userData.user = parsedUserData.user;
      } else {
        (this as any).userData.user = parsedUserData;
      }
    } else {
      console.log("money_management_user key not found in local storage");
    }
  },
  methods: {
    forceRemount() {
      (this as any).componentKey++;
    },
    handleUserData(variable: UserData) {
      (this as any).userData.user = variable;
    }
  }

}
</script>

<style scoped>
.component-container {
  width: 100%;
  min-height: 100vh;
  background: transparent;
}

.centered-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: transparent;
}
</style>