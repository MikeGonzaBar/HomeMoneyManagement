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
import { getStoredSession, type SessionUser } from '@/services/session'
interface UserData {
  first_name: string,
  id: number,
  last_name: string,
  password: string,
  status: string,
  username: string,
}
interface User {
  user: SessionUser
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
    const session = getStoredSession();
    if (session) {
      (this as any).userData.user = session.user;
    }
  },
  methods: {
    forceRemount() {
      (this as any).componentKey++;
    },
    handleUserData(variable: SessionUser) {
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
