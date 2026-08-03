import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import InterviewView from '@/views/InterviewView.vue'
import MetaAuthoringStartView from '@/views/MetaAuthoringStartView.vue'
import PublicationView from '@/views/PublicationView.vue'

export const routes = [
  {
    path: '/',
    redirect: { name: 'session-placeholder' },
  },
  {
    path: '/sessions',
    name: 'session-placeholder',
    component: InterviewView,
    meta: { roles: ['respondent'] },
  },
  {
    path: '/sessions/:sessionId',
    name: 'session',
    component: InterviewView,
    meta: { roles: ['respondent'] },
    props: true,
  },
  {
    path: '/authoring',
    name: 'meta-authoring',
    component: MetaAuthoringStartView,
    meta: { roles: ['author'] },
  },
  {
    path: '/authoring/sessions/:sessionId',
    name: 'meta-authoring-session',
    component: InterviewView,
    meta: { roles: ['author', 'respondent'] },
    props: true,
  },
  {
    path: '/sessions/:sessionId/publication',
    name: 'publication',
    component: PublicationView,
    meta: { roles: ['publisher'] },
    props: true,
  },
] satisfies RouteRecordRaw[]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router