import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import History from '../views/History.vue'
import SimulatorChat from '../views/SimulatorChat.vue';
import Selection from '../views/Selection.vue'
import MapPage from '../views/MapPage.vue'
import MapSelection from '../views/MapSelection.vue';
import MapSimulatorChat from '../components/MapSimulatorChat.vue'
import MapSimulatorPage from '../views/MapSimulatorPage.vue'
import MapChat from '../views/MapChat.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/chat', component: Chat },
  { path: '/history', component: History },
  { path: '/simulator', name: 'Simulator', component: SimulatorChat },
  { path: '/selection', name:'Selection', component: Selection},
  { path: '/mappage', name:'MapPage', component: MapPage},
  { path: '/mapselection', name:'MapSelection', component: MapSelection},
  { path: '/mapsimulatorchat', name:'MapSimulatorChat', component: MapSimulatorChat},
  { path: '/mapsimulatorpage', name:'MapSimulatorPage', component: MapSimulatorPage},
  { path: '/mapchat', name: 'MapChat', component: MapChat}
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router