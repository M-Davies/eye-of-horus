import { render, screen } from '@testing-library/react';
import App from '../../App';

test('renders navbar link', () => {
  render(<App />);
  const linkElement = screen.getByText(/Eye Of Horus/);
  expect(linkElement).toBeInTheDocument();
});
