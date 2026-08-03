import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import catalog from '../../../data/components/catalog.v1.json'
import SemanticRenderer from '../../src/components/interview/SemanticRenderer.vue'
import {
  catalogComponentNames,
  resolveRenderer,
  type ComponentSpec,
} from '../../src/components/renderers/registry'

const spec = (name: string, fallback?: string, props: Record<string, unknown> = {}): ComponentSpec => ({
  name,
  version: 1,
  props,
  fallback,
})

const objectSchema = {
  type: 'object',
  properties: { value: { type: 'string', title: 'Value' } },
}
const arraySchema = { type: 'array', items: objectSchema }

describe('SemanticRenderer', () => {
  it('resolves known components and reports shape incompatibility explicitly', () => {
    expect(resolveRenderer(spec('short_text'), { type: 'string' }, options()).resolvedName).toBe('short_text')

    const incompatible = resolveRenderer(spec('number'), { type: 'string' }, options())
    expect(incompatible.supported).toBe(false)
    expect(incompatible.reason).toContain('incompatible')
  })

  it('requires a registered, schema-compatible explicit fallback', () => {
    const missing = resolveRenderer(spec('unknown'), { type: 'string' }, options())
    expect(missing.reason).toBe('Component "unknown" is not registered.')

    const compatible = resolveRenderer(spec('unknown', 'short_text'), { type: 'string' }, options())
    expect(compatible).toMatchObject({ supported: true, resolvedName: 'short_text', usedFallback: true })

    const incompatible = resolveRenderer(spec('unknown', 'number'), { type: 'string' }, options())
    expect(incompatible.supported).toBe(false)
    expect(incompatible.reason).toContain('fallback "number" is incompatible')
  })

  it('covers every checked-in catalog name with a compatible representative schema', () => {
    const schemasByShape: Record<string, Record<string, unknown>> = {
      string: { type: 'string' },
      number: { type: 'number' },
      boolean: { type: 'boolean' },
      scalar: { type: 'string', enum: ['choice-a', 'choice-b'] },
      object: objectSchema,
      array: { type: 'array', items: { type: 'string', enum: ['choice-a', 'choice-b'] } },
      asset_reference_array: arraySchema,
      money: { type: 'number' },
      date: { type: 'string' },
      datetime: { type: 'string' },
    }

    expect(catalogComponentNames).toEqual(catalog.components.map((entry) => entry.name))
    for (const entry of catalog.components) {
      const isProgramme = entry.name === 'declared_programme'
      const schema = isProgramme
        ? {
            type: 'object',
            properties: {
              selections: {
                type: 'array',
                items: {
                  type: 'object',
                  required: ['item_id', 'status'],
                  properties: {
                    item_id: { type: 'string', enum: ['item-a'] },
                    status: { type: 'string', enum: ['required'] },
                  },
                },
              },
            },
          }
        : ['repeatable_group'].includes(entry.name)
          ? arraySchema
          : schemasByShape[entry.answer_shape]
      if (!schema) throw new Error(`Missing representative schema for ${entry.answer_shape}`)
      const resolution = resolveRenderer(
        spec(
          entry.name,
          undefined,
          isProgramme
            ? {
                groups: [{ id: 'group-a', label: 'Group A', items: [{ value: 'item-a', label: 'Item A' }] }],
                statuses: [{ value: 'required', label: 'Required' }],
              }
            : {},
        ),
        schema,
        options(),
      )
      expect(resolution.supported, `${entry.name}: ${resolution.reason}`).toBe(true)
    }
  })

  it('preserves a stable choice ID emitted by the production choice renderer', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('single_select', undefined, {
          options: [
            { value: 'machine-a', label: 'Display A' },
            { value: 'machine-b', label: 'Display B' },
          ],
        }),
        answerSchema: { type: 'string', enum: ['machine-a', 'machine-b'] },
        draftValue: 'machine-a',
        prompt: 'Choose one',
      },
    })

    await wrapper.findAll('input')[1]?.trigger('change')
    expect(wrapper.emitted('update:modelValue')).toEqual([['machine-b']])
  })

  it('uses server-resolved structured fields when object properties are not repeated', () => {
    const resolution = resolveRenderer(
      spec('structured_form', undefined, {
        fields: [
          {
            component: 'single_select',
            key: 'build_type',
            label: 'What kind of project is this?',
            options: ['New build', 'Renovation'],
          },
        ],
      }),
      { type: 'object', required: ['build_type'] },
      options(),
    )

    expect(resolution).toMatchObject({
      supported: true,
      props: {
        fields: [
          {
            key: 'build_type',
            label: 'What kind of project is this?',
            required: true,
            type: 'select',
            options: [
              { value: 'New build', label: 'New build' },
              { value: 'Renovation', label: 'Renovation' },
            ],
          },
        ],
      },
    })
  })

  it('renders declared nested multi-select and measurement controls with typed values', async () => {
    const answerSchema = {
      type: 'object',
      required: ['ceiling_preferences', 'target_area'],
      properties: {
        ceiling_preferences: {
          type: 'array',
          items: { type: 'string', enum: ['raised', 'vaulted'] },
        },
        target_area: {
          type: 'object',
          required: ['value', 'unit'],
          properties: {
            value: { type: 'number', minimum: 1 },
            unit: { type: 'string', enum: ['sq_ft', 'sq_m'] },
          },
        },
      },
    }
    const componentSpec = spec('structured_form', undefined, {
      fields: [
        {
          key: 'ceiling_preferences',
          label: 'Ceiling preferences',
          component: 'multi_select',
            help_text: 'Choose every preference that applies.',
            example: 'Raised ceilings in the living area.',
          options: [
            { value: 'raised', label: 'Raised ceilings' },
            { value: 'vaulted', label: 'Vaulted living area' },
          ],
        },
        {
          key: 'target_area',
          label: 'Approximate finished living area',
          component: 'measurement',
          unit_options: [
            { value: 'sq_ft', label: 'Square feet' },
            { value: 'sq_m', label: 'Square metres' },
          ],
        },
      ],
    })

    const resolution = resolveRenderer(componentSpec, answerSchema, options())
    expect(resolution.props).toMatchObject({
      fields: [
        { key: 'ceiling_preferences', type: 'multi_select', required: true },
        { key: 'target_area', type: 'measurement', required: true },
      ],
    })

    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec,
        answerSchema,
        draftValue: {
          ceiling_preferences: [],
          target_area: { value: null, unit: null },
        },
        label: 'Home structure',
      },
    })

    expect(wrapper.find('textarea').exists()).toBe(false)
    expect(wrapper.text()).toContain('Choose every preference that applies.')
    expect(wrapper.text()).toContain('Raised ceilings in the living area.')
    const choices = wrapper.findAll('input[type="checkbox"]')
    expect(choices).toHaveLength(2)
    await choices[0]!.setValue(true)
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toEqual({
      ceiling_preferences: ['raised'],
      target_area: { value: null, unit: null },
    })

    const valueInput = wrapper.get('input[type="number"]')
    await valueInput.setValue('1200')
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toEqual({
      ceiling_preferences: [],
      target_area: { value: 1200, unit: null },
    })

    await wrapper.get('select').setValue('1')
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toEqual({
      ceiling_preferences: [],
      target_area: { value: null, unit: 'sq_m' },
    })
  })

  it('gives local feedback for invalid nested selections and measurements', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('structured_form', undefined, {
          fields: [
            {
              key: 'needs',
              label: 'Relevant needs',
              component: 'multi_select',
              options: [{ value: 'private-room', label: 'Private bedroom' }],
            },
            {
              key: 'target_area',
              label: 'Approximate finished living area',
              component: 'measurement',
              unit_options: [{ value: 'sq_ft', label: 'Square feet' }],
            },
          ],
        }),
        answerSchema: {
          type: 'object',
          required: ['needs', 'target_area'],
          properties: {
            needs: { type: 'array', items: { type: 'string', enum: ['private-room'] } },
            target_area: {
              type: 'object',
              required: ['value', 'unit'],
              properties: {
                value: { type: 'number', minimum: 1 },
                unit: { type: 'string', enum: ['sq_ft'] },
              },
            },
          },
        },
        draftValue: {
          needs: [],
          target_area: { value: null, unit: null },
        },
        label: 'Home structure',
      },
    })

    const needsChoice = wrapper.get('input[type="checkbox"]')
    await needsChoice.setValue(true)
    await needsChoice.setValue(false)
    expect(wrapper.get('[role="alert"]').text()).toContain('Select at least one option.')

    await wrapper.get('input[type="number"]').setValue('0')
    await wrapper.setProps({
      draftValue: { needs: [], target_area: { value: 0, unit: null } },
    })
    expect(wrapper.findAll('[role="alert"]').map((alert) => alert.text())).toContain(
      'Enter a value of at least 1.',
    )
  })

  it('initializes added repeatable items with nested multi-select and measurement defaults', async () => {
    const answerSchema = {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          needs: { type: 'array', items: { type: 'string', enum: ['private-room'] } },
          target_area: {
            type: 'object',
            properties: {
              value: { type: 'number' },
              unit: { type: 'string', enum: ['sq_ft'] },
            },
          },
        },
      },
    }
    const componentSpec = spec('repeatable_group', undefined, {
      fields: [
        {
          key: 'needs',
          label: 'Relevant needs',
          component: 'multi_select',
          options: [{ value: 'private-room', label: 'Private bedroom' }],
        },
        {
          key: 'target_area',
          label: 'Approximate finished living area',
          component: 'measurement',
          unit_options: [{ value: 'sq_ft', label: 'Square feet' }],
        },
      ],
    })

    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec,
        answerSchema,
        draftValue: [],
        label: 'Household members',
      },
    })

    await wrapper.get('.repeatable-group__add').trigger('click')
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toEqual([
      { needs: [], target_area: { value: null, unit: null } },
    ])
  })

  it('renders declared repeatable controls when the item schema is open-ended', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('repeatable_group', undefined, {
          fields: [
            { key: 'relationship', label: 'Relationship or role', component: 'short_text' },
            {
              key: 'life_stage',
              label: 'Life stage',
              component: 'single_select',
              options: ['Young child', 'Adult'],
            },
            {
              key: 'needs',
              label: 'Relevant needs',
              component: 'multi_select',
              options: ['Private bedroom'],
            },
          ],
        }),
        answerSchema: { type: 'array' },
        draftValue: [],
        label: 'Household members',
      },
    })

    expect(wrapper.find('textarea').exists()).toBe(false)
    await wrapper.get('.repeatable-group__add').trigger('click')
    await wrapper.setProps({
      draftValue: wrapper.emitted('update:modelValue')?.at(-1)?.[0],
    })
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    expect(wrapper.find('select').exists()).toBe(true)
    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true)
  })

  it('renders an unanswered structured form with an empty object draft', () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('structured_form', undefined, {
          fields: [
            {
              component: 'single_select',
              key: 'build_type',
              label: 'What kind of project is this?',
              options: ['New build', 'Renovation'],
            },
          ],
        }),
        answerSchema: { type: 'object', required: ['build_type'] },
        draftValue: null,
        label: 'Project basics',
      },
    })

    expect(wrapper.find('select').exists()).toBe(true)
    expect(wrapper.find('[data-unsupported-component]').exists()).toBe(false)
  })

  it('captures an unconstrained object as valid JSON', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('structured_form'),
        answerSchema: { type: 'object' },
        draftValue: null,
        label: 'Output contract',
      },
    })

    expect(wrapper.get('label').text()).toBe('Advanced JSON object input')
    const editor = wrapper.get('textarea')
    await editor.setValue('{"type":"object","properties":{"name":{"type":"string"}}}')

    expect(wrapper.find('[data-unsupported-component]').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')).toEqual([
      [{ type: 'object', properties: { name: { type: 'string' } } }],
    ])
  })

  it('captures an unconstrained object collection as valid JSON', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('repeatable_group'),
        answerSchema: { type: 'array', items: { type: 'object' } },
        draftValue: null,
        label: 'Questions',
      },
    })

    expect(wrapper.get('label').text()).toBe('Advanced JSON array input')
    const editor = wrapper.get('textarea')
    await editor.setValue('[{"id":"project-name","prompt":"What is the project name?"}]')

    expect(wrapper.find('[data-unsupported-component]').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')).toEqual([
      [[{ id: 'project-name', prompt: 'What is the project name?' }]],
    ])
  })

  it.each([
    ['number', { type: 'number' }, 42],
    ['boolean', { type: 'boolean' }, false],
    ['structured_form', objectSchema, { value: 'kept' }],
    ['repeatable_group', arraySchema, [{ value: 'kept' }]],
  ])('submits the current %s draft without coercion', async (name, answerSchema, draftValue) => {
    const wrapper = mount(SemanticRenderer, {
      props: { componentSpec: spec(name), answerSchema, draftValue, label: 'Answer' },
    })

    await wrapper.get('.semantic-renderer__submit').trigger('click')
    expect(wrapper.emitted('submit')?.[0]?.[0]).toBe(draftValue)
  })

  it('recursively renders nested repeatable groups', async () => {
    const nestedArraySchema = {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string', title: 'Name' },
          windows: {
            type: 'array',
            title: 'Windows',
            items: {
              type: 'object',
              properties: { width: { type: 'number', title: 'Width' } },
            },
          },
        },
      },
    }
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('repeatable_group'),
        answerSchema: nestedArraySchema,
        draftValue: [{ name: 'Kitchen', windows: [{ width: 3 }] }],
        label: 'Rooms',
      },
    })

    // Nested collection legend and pre-populated nested scalar render.
    expect(wrapper.text()).toContain('Windows')
    const numberInputs = wrapper.findAll('input[type="number"]')
    const widthInput = numberInputs.find(
      (input) => (input.element as HTMLInputElement).value === '3',
    )
    expect(widthInput).toBeDefined()

    // Editing a nested scalar propagates up through the recursive tree.
    await widthInput!.setValue('5')
    const updates = wrapper.emitted('update:modelValue')
    expect(updates?.at(-1)?.[0]).toEqual([{ name: 'Kitchen', windows: [{ width: 5 }] }])
  })

  it('renders a declared programme and emits stable selections without JSON input', async () => {
    const componentSpec = spec('declared_programme', undefined, {
      groups: [
        {
          id: 'living',
          label: 'Living spaces',
          items: [
            { value: 'great_room', label: 'Great room' },
            { value: 'reading_nook', label: 'Reading nook' },
          ],
        },
      ],
      statuses: [
        { value: 'required', label: 'Required' },
        { value: 'possible', label: 'Possible' },
      ],
      details: [
        {
          key: 'size',
          label: 'Preferred size',
          component: 'single_select',
          options: [
            { value: 'compact', label: 'Compact' },
            { value: 'generous', label: 'Generous' },
          ],
        },
        {
          key: 'notes',
          label: 'Notes',
          component: 'long_text',
        },
      ],
    })
    const answerSchema = {
      type: 'object',
      required: ['selections'],
      properties: {
        selections: {
          type: 'array',
          items: {
            type: 'object',
            required: ['item_id', 'status'],
            properties: {
              item_id: { type: 'string', enum: ['great_room', 'reading_nook'] },
              status: { type: 'string', enum: ['required', 'possible'] },
              details: {
                type: 'object',
                properties: {
                  size: { type: 'string', enum: ['compact', 'generous'] },
                  notes: { type: 'string' },
                },
              },
            },
          },
        },
      },
    }
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec,
        answerSchema,
        draftValue: { selections: [] },
        label: 'Spaces',
      },
    })

    expect(wrapper.find('textarea').exists()).toBe(false)
    expect(wrapper.text()).toContain('Living spaces')
    expect(wrapper.text()).toContain('Great room')

    await wrapper.get('[data-programme-item="great_room"] select').setValue('required')
    const selected = { selections: [{ item_id: 'great_room', status: 'required' }] }
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toEqual(selected)

    await wrapper.setProps({ draftValue: selected })
    await wrapper.get('[data-programme-item="great_room"] textarea').setValue('North-facing windows')
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toEqual({
      selections: [
        {
          item_id: 'great_room',
          status: 'required',
          details: { notes: 'North-facing windows' },
        },
      ],
    })
  })

  it('initializes an unanswered declared programme with empty selections', () => {
    const resolution = resolveRenderer(
      spec('declared_programme', undefined, {
        groups: [{ id: 'group-a', label: 'Group A', items: [{ value: 'item-a', label: 'Item A' }] }],
        statuses: [{ value: 'required', label: 'Required' }],
      }),
      {
        type: 'object',
        properties: {
          selections: {
            type: 'array',
            items: {
              type: 'object',
              required: ['item_id', 'status'],
              properties: {
                item_id: { type: 'string', enum: ['item-a'] },
                status: { type: 'string', enum: ['required'] },
              },
            },
          },
        },
      },
      options(),
    )

    expect(resolution).toMatchObject({ supported: true, props: { modelValue: { selections: [] } } })
  })

  it('shows malformed declared programmes as unsupported instead of JSON fallback', () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('declared_programme', undefined, {
          groups: [{ id: 'group-a', label: 'Group A', items: [{ value: 'item-a', label: 'Item A' }] }],
        }),
        answerSchema: {
          type: 'object',
          properties: {
            selections: {
              type: 'array',
              items: {
                type: 'object',
                required: ['item_id', 'status'],
                properties: {
                  item_id: { type: 'string', enum: ['item-a'] },
                  status: { type: 'string', enum: ['required'] },
                },
              },
            },
          },
        },
        draftValue: { selections: [] },
        label: 'Items',
      },
    })

    expect(wrapper.find('[data-unsupported-component]').exists()).toBe(true)
    expect(wrapper.find('textarea').exists()).toBe(false)
  })

  it('reuses declared programme vocabulary without coupling emitted values to labels', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('declared_programme', undefined, {
          groups: [
            {
              id: 'services',
              label: 'Platform services',
              items: [{ value: 'audit_stream', label: 'Compliance event feed' }],
            },
          ],
          statuses: [
            { value: 'adopt', label: 'Use in the first release' },
            { value: 'defer', label: 'Consider later' },
          ],
        }),
        answerSchema: {
          type: 'object',
          required: ['selections'],
          properties: {
            selections: {
              type: 'array',
              items: {
                type: 'object',
                required: ['item_id', 'status'],
                properties: {
                  item_id: { type: 'string', enum: ['audit_stream'] },
                  status: { type: 'string', enum: ['adopt', 'defer'] },
                },
              },
            },
          },
        },
        draftValue: { selections: [] },
        label: 'Service choices',
      },
    })

    expect(wrapper.text()).toContain('Compliance event feed')
    expect(wrapper.text()).toContain('Use in the first release')
    await wrapper.get('[data-programme-item="audit_stream"] select').setValue('adopt')
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toEqual({
      selections: [{ item_id: 'audit_stream', status: 'adopt' }],
    })
  })

  it('renders an accessible explicit unsupported state', () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('number'),
        answerSchema: { type: 'object' },
        draftValue: {},
        label: 'Answer',
      },
    })

    expect(wrapper.get('[role="alert"]').text()).toContain('incompatible')
    expect(wrapper.find('.semantic-renderer__submit').exists()).toBe(false)
  })
})

function options() {
  return { label: 'Answer', draftValue: null }
}
