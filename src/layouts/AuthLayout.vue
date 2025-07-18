<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <q-page class="flex flex-center">
        <q-card class="login-card">
          <q-card-section class="text-center">
            <div class="row q-gutter-md items-center">
              <div class="col-5">
                <ozone-logo />
              </div>
              <div class="col-auto text-h4 text-left">
                {{ route.meta.header }}
              </div>
            </div>
          </q-card-section>
          <q-card-section>
            <router-view />
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import OzoneLogo from "components/OzoneLogo.vue";
import { useRoute } from "vue-router";

const route = useRoute();
</script>

<style scoped lang="scss">
.login-card {
  width: 100%;
  padding: 20px;
  max-width: 500px;
}
</style>
