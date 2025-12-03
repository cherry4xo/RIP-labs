// src/store/cartSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { API_BASE_URL } from '../config/api.config';
import type { AssessmentReportDetails, AssessmentBasketInfo } from '../types/api';

interface CartState {
  cart: AssessmentReportDetails | null;
  basketInfo: AssessmentBasketInfo | null;
  loading: boolean;
  error: string | null;
}

const initialState: CartState = {
  cart: null,
  basketInfo: null,
  loading: false,
  error: null,
};

// Async thunks
export const fetchBasketInfo = createAsyncThunk(
  'cart/fetchBasketInfo',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const token = state.auth.token;

      const response = await axios.get(`${API_BASE_URL}/report/draft/info`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Ошибка загрузки корзины');
    }
  }
);

export const addToCart = createAsyncThunk(
  'cart/addToCart',
  async (assessmentId: number, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const token = state.auth.token;

      const response = await axios.post(
        `${API_BASE_URL}/report/draft/assessments`,
        { assessment_id: assessmentId },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Ошибка добавления в корзину');
    }
  }
);

export const removeFromCart = createAsyncThunk(
  'cart/removeFromCart',
  async (assessmentId: number, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const token = state.auth.token;

      const response = await axios.delete(
        `${API_BASE_URL}/report/draft/assessments/${assessmentId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Ошибка удаления из корзины');
    }
  }
);

export const updateCartItem = createAsyncThunk(
  'cart/updateCartItem',
  async (
    {
      assessmentId,
      data,
    }: {
      assessmentId: number;
      data: { protection_level: string; comment?: string };
    },
    { getState, rejectWithValue }
  ) => {
    try {
      const state = getState() as any;
      const token = state.auth.token;

      const response = await axios.put(
        `${API_BASE_URL}/report/draft/assessments/${assessmentId}`,
        data,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Ошибка обновления элемента');
    }
  }
);

export const submitCart = createAsyncThunk(
  'cart/submitCart',
  async (targetSystemInfo: string, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const token = state.auth.token;
      const reportId = state.cart.basketInfo?.report_id;

      if (!reportId || reportId === -1) {
        return rejectWithValue('Корзина пуста');
      }

      const response = await axios.put(
        `${API_BASE_URL}/reports/${reportId}/form`,
        { target_system_info: targetSystemInfo },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Ошибка отправки заявки');
    }
  }
);

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    clearCart: (state) => {
      state.cart = null;
      state.basketInfo = null;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch basket info
    builder
      .addCase(fetchBasketInfo.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchBasketInfo.fulfilled, (state, action) => {
        state.loading = false;
        state.basketInfo = action.payload;
      })
      .addCase(fetchBasketInfo.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Add to cart
    builder
      .addCase(addToCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addToCart.fulfilled, (state, action) => {
        state.loading = false;
        state.cart = action.payload;
        state.basketInfo = {
          report_id: action.payload.id,
          item_count: action.payload.components.length,
        };
      })
      .addCase(addToCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Remove from cart
    builder
      .addCase(removeFromCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeFromCart.fulfilled, (state, action) => {
        state.loading = false;
        state.cart = action.payload;
        state.basketInfo = {
          report_id: action.payload.id,
          item_count: action.payload.components.length,
        };
      })
      .addCase(removeFromCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Update cart item
    builder
      .addCase(updateCartItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateCartItem.fulfilled, (state, action) => {
        state.loading = false;
        state.cart = action.payload;
      })
      .addCase(updateCartItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Submit cart
    builder
      .addCase(submitCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitCart.fulfilled, (state) => {
        state.loading = false;
        state.cart = null;
        state.basketInfo = null;
      })
      .addCase(submitCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearCart, clearError } = cartSlice.actions;
export default cartSlice.reducer;
