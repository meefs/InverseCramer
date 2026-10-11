import motionCanvasModule from '@motion-canvas/vite-plugin';
import ffmpegModule from '@motion-canvas/ffmpeg';
import {defineConfig} from 'vite';

// The published CJS builds expose the plugin factory on `.default`
const motionCanvas = (motionCanvasModule as any).default ?? motionCanvasModule;
const ffmpeg = (ffmpegModule as any).default ?? ffmpegModule;

export default defineConfig({
  plugins: [motionCanvas(), ffmpeg()],
});
