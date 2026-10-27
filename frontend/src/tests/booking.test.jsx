import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { DoctorsDirectory } from '../pages/patient/DoctorsDirectory';
import { AuthProvider } from '../context/AuthContext';

describe('Doctors Directory and Booking UI Tests', () => {
  it('renders search filter controls', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <DoctorsDirectory />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByPlaceholderText(/Search by doctor name or condition/i)).toBeInTheDocument();
    expect(screen.getByText(/All Specializations/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Apply Filters/i })).toBeInTheDocument();
  });
});
