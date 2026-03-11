import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

describe('LoadingSpinner', () => {
  it('should render when isLoading is true', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        isLoading: true,
        message: 'Loading...',
      },
    })
    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
    expect(wrapper.text()).toContain('Loading...')
  })

  it('should not render when isLoading is false', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        isLoading: false,
      },
    })
    expect(wrapper.find('.loading-spinner').exists()).toBe(false)
  })

  it('should display custom message', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        isLoading: true,
        message: 'Custom message',
      },
    })
    expect(wrapper.text()).toContain('Custom message')
  })
})
