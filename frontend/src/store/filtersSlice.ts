// src/store/filtersSlice.ts
import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from './store';

interface FiltersState {
  searchQuery: string;
}

const initialState: FiltersState = {
  searchQuery: '',
};

export const filtersSlice = createSlice({
  name: 'filters',
  initialState,
  reducers: {
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    resetFilters: (state) => {
      state.searchQuery = '';
    },
  },
});

export const { setSearchQuery, resetFilters } = filtersSlice.actions;

export const selectSearchQuery = (state: RootState) => state.filters.searchQuery;

export default filtersSlice.reducer;
