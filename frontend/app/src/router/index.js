import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import History from '../views/History.vue'
import SimulatorChat from '../views/SimulatorChat.vue';
import Selection from '../views/Selection.vue'


const routes = [
  { path: '/', component: Home },
  { path: '/chat', component: Chat },
  { path: '/history', component: History },
  { path: '/simulator', name: 'Simulator', component: SimulatorChat },
  { path: '/selection', name:'Selection', component: Selection}
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router