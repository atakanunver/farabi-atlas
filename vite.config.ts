import { defineConfig } from 'vite';
export default defineConfig({base:'/kure/',server:{port:5173,proxy:{'/api/atlas':'http://127.0.0.1:8099'}},build:{target:'es2020',chunkSizeWarningLimit:1200}});
