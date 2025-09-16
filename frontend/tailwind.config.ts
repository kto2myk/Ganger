import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx,js,jsx}',
    './components/**/*.{ts,tsx,js,jsx}',
    './lib/**/*.{ts,tsx,js,jsx}'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#0F172A',
          accent: '#6366F1'
        }
      },
      borderRadius: {
        xl: '1rem'
      }
    }
  },
  plugins: []
};
export default config;
