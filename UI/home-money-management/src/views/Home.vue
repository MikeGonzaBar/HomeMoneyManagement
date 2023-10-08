<template>
  <div class="component-container">

    <div v-if="Object.keys(userData).length == 0" class="centered-container">
      <LoginRegister @userDataSent="handleUserData" />
    </div>


    <MainPage v-else :userData="userData" />

  </div>
</template>

<script lang="ts">
import LoginRegister from '@/components/LoginRegister.vue'
import MainPage from '@/components/MainPage.vue'

export default {
  name: 'App',
  components: {
    LoginRegister,
    MainPage
  },
  data() {
    return {
      userData: {}
    };
  },
  mounted() {
    // Get the value of the money_management_user key from localStorage
    const userDataString = localStorage.getItem('money_management_user');
    if (userDataString !== null) {
      console.log("userData keys: ", Object.keys(this.userData).length);
      this.userData = JSON.parse(userDataString);
      console.log("userData on load: ", this.userData);
    } else {
      console.log("money_management_user key not found in local storage");
    }
    console.log("userData keys: ", Object.keys(this.userData).length);
  },
  methods: {
    handleUserData(variable: object) {
      console.log('Received variable from child:', variable);
      this.userData = variable;
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