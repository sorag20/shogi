import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Board from '../../components/Board.vue'
import type { BoardState } from '../../types/shogi'

describe('Board Component', () => {
  const createEmptyBoard = (): BoardState => ({
    board: Array(9)
      .fill(null)
      .map(() => Array(9).fill(null)),
    hands: {
      black: { pawn: 0, lance: 0, knight: 0, silver: 0, gold: 0, bishop: 0, rook: 0, king: 0 },
      white: { pawn: 0, lance: 0, knight: 0, silver: 0, gold: 0, bishop: 0, rook: 0, king: 0 },
    },
    turn: 'black',
  })

  it('should render a 9x9 board', () => {
    const wrapper = mount(Board, {
      props: {
        initialBoard: createEmptyBoard(),
      },
    })

    const squares = wrapper.findAll('.square')
    expect(squares).toHaveLength(81) // 9x9
  })

  it('should display pieces on the board', () => {
    const board = createEmptyBoard()
    board.board[0][0] = { type: 'pawn', owner: 'black', promoted: false }

    const wrapper = mount(Board, {
      props: {
        initialBoard: board,
      },
    })

    const pieces = wrapper.findAll('.piece')
    expect(pieces.length).toBeGreaterThan(0)
  })

  it('should select a square when clicked', async () => {
    const wrapper = mount(Board, {
      props: {
        initialBoard: createEmptyBoard(),
        editable: true,
      },
    })

    const squares = wrapper.findAll('.square')
    await squares[0].trigger('click')

    expect(squares[0].classes()).toContain('selected')
  })

  it('should display turn information', () => {
    const board = createEmptyBoard()
    board.turn = 'black'

    const wrapper = mount(Board, {
      props: {
        initialBoard: board,
      },
    })

    expect(wrapper.text()).toContain('先手')
  })

  it('should emit update:board event when board changes', async () => {
    const wrapper = mount(Board, {
      props: {
        initialBoard: createEmptyBoard(),
        editable: true,
      },
    })

    const switchTurnBtn = wrapper.find('.btn')
    await switchTurnBtn.trigger('click')

    expect(wrapper.emitted('update:board')).toBeTruthy()
  })

  it('should not allow editing when editable is false', async () => {
    const wrapper = mount(Board, {
      props: {
        initialBoard: createEmptyBoard(),
        editable: false,
      },
    })

    const squares = wrapper.findAll('.square')
    await squares[0].trigger('click')

    // Should not emit update event
    expect(wrapper.emitted('update:board')).toBeFalsy()
  })

  it('should clear board when clear button is clicked', async () => {
    const board = createEmptyBoard()
    board.board[0][0] = { type: 'pawn', owner: 'black', promoted: false }

    const wrapper = mount(Board, {
      props: {
        initialBoard: board,
        editable: true,
      },
    })

    const clearBtn = wrapper.findAll('.btn-danger')[0]
    await clearBtn.trigger('click')

    const emitted = wrapper.emitted('update:board')
    expect(emitted).toBeTruthy()
  })
})
