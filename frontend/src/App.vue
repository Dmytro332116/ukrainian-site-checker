<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>
        <v-icon class="mr-2">mdi-web-check</v-icon>
        Ukrainian Site Checker
      </v-toolbar-title>
      
      <v-spacer></v-spacer>
      
      <v-btn to="/" text>
        <v-icon left>mdi-view-dashboard</v-icon>
        Дашборд
      </v-btn>
      
      <v-btn to="/websites" text>
        <v-icon left>mdi-web</v-icon>
        Сайти
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>
    
    <v-footer app>
      <v-spacer></v-spacer>
      <span class="text-caption">
        © 2025 Ukrainian Site Checker v1.0.0
      </span>
    </v-footer>
  </v-app>
</template>

<script setup>
// Main app component
</script>

<style scoped>
/* Custom styles if needed */
</style>

