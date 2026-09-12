import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'

const source = readFileSync(new URL('../app/pages/agents-create.vue', import.meta.url), 'utf8')
const script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1]
const requests = []
const navigations = []
let create = async (payload) => {
  requests.push(payload)
  return { id: 'new-agent' }
}
const context = vm.createContext({
  exports: {},
  require: () => ({ useApiAgents: () => ({ create: payload => create(payload) }) }),
  ref: value => ({ value }),
  reactive: value => value,
  computed: getter => ({ get value() { return getter() } }),
  definePageMeta: meta => assert.equal(meta.path, '/agents/create'),
  useHead: () => {},
  navigateTo: location => navigations.push(location)
})
vm.runInContext(ts.transpileModule(`${script}\nglobalThis.test = { form, saving, error, saveAgent, selectPreset };`, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
}).outputText, context)
const { form, saving, error, saveAgent, selectPreset } = context.test

await saveAgent()
assert.equal(requests.length, 0)
assert.match(error.value, /required/)
form.name = '   '
await saveAgent()
assert.equal(requests.length, 0)
form.name = ' Researcher '
form.model = ' '
await saveAgent()
assert.equal(requests.length, 0)
form.model = ' llama3.1 '
selectPreset('Research')
assert.equal(form.category, 'Research')
selectPreset('Support')
assert.equal(form.category, 'Custom')
Object.assign(form, {
  role_title: ' Analyst ', description: ' Summary ', system_prompt: ' Cite sources ',
  status: 'inactive', type: 'rag', tagsInput: ' research, , reports ',
  capabilitiesInput: ' Find sources\n\n Summarize ', toolsInput: ' Search, , Notion '
})
await saveAgent()
assert.deepEqual(JSON.parse(JSON.stringify(requests[0])), {
  name: 'Researcher', role_title: 'Analyst', category: 'Custom', model: 'llama3.1',
  description: 'Summary', system_prompt: 'Cite sources', status: 'inactive', type: 'rag',
  tags: ['research', 'reports'], capabilities: ['Find sources', 'Summarize'],
  tools: ['Search', 'Notion'], uses_count: 0, completion_rate: 100
})
assert.equal(navigations[0].path, '/agents')
assert.equal(navigations[0].query.created, 'new-agent')
assert.equal(saving.value, false)

create = async () => {
  throw { data: { detail: 'Service unavailable' } }
}
await saveAgent()
assert.equal(error.value, 'Service unavailable')
assert.equal(form.name, ' Researcher ')
assert.equal(saving.value, false)
assert.equal(navigations.length, 1)

let release
let calls = 0
create = () => {
  calls++
  return new Promise((resolve) => {
    release = resolve
  })
}
const pending = saveAgent()
assert.equal(saving.value, true)
await saveAgent()
assert.equal(calls, 1)
release({ id: 'retry-agent' })
await pending
assert.equal(saving.value, false)
assert.equal(error.value, '')

const agentsPage = readFileSync(new URL('../app/pages/agents.vue', import.meta.url), 'utf8')
assert.equal(agentsPage.includes('openCreateModal'), false)
assert.equal(agentsPage.includes('api.agents.create('), false)
assert.equal((agentsPage.match(/@click="goToCreateAgent"/g) || []).length, 4)
assert.match(agentsPage, /navigateTo\('\/agents\/create'\)/)
const dropdown = readFileSync(new URL('../app/components/WorkspaceDropdown.vue', import.meta.url), 'utf8')
assert.match(dropdown, /to="\/agents\/create"/)
console.log('Create agent checks passed: validation, all fields, presets, navigation, errors, duplicate guard, entry points.')
