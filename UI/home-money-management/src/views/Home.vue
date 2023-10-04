<template>
  <div class="component-container">
    <template v-if="userData !== null">
      <HelloWorld />
    </template>
    <template v-else>
      <div class="centered-container">
        <LoginRegister @userDataSent="handleUserData" />
      </div>
    </template>
  </div>
</template>

<script>
import LoginRegister from '@/components/LoginRegister.vue'
import HelloWorld from '@/components/HelloWorld.vue'

export default {
  name: 'App',
  components: {
    LoginRegister,
    HelloWorld
  },
  data() {
    return {
      userData: null
    };
  },
  methods: {
    handleUserData(variable) {
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