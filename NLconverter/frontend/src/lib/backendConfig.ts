import fs from 'fs';
import path from 'path';

function parseEnvFile(filePath: string): Record<string, string> {
  if (!fs.existsSync(filePath)) return {};

  return fs.readFileSync(filePath, 'utf8')
    .split(/\r?\n/)
    .reduce<Record<string, string>>((acc, line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) return acc;

      const separatorIndex = trimmed.indexOf('=');
      if (separatorIndex === -1) return acc;

      const key = trimmed.slice(0, separatorIndex).trim();
      const rawValue = trimmed.slice(separatorIndex + 1).trim();
      const value = rawValue.replace(/^['"]|['"]$/g, '');

      if (key) {
        acc[key] = value;
      }

      return acc;
    }, {});
}

export function getBackendConfig() {
  const candidates = [
    process.cwd(),
    path.resolve(process.cwd(), 'frontend'),
    path.resolve(process.cwd(), '..'),
    path.resolve(process.cwd(), '../frontend'),
  ];

  const env: Record<string, string> = {};

  for (const baseDir of candidates) {
    for (const fileName of ['.env.local', '.env']) {
      Object.assign(env, parseEnvFile(path.join(baseDir, fileName)));
    }
  }

  return {
    BACKEND_URL: process.env.BACKEND_URL || env.BACKEND_URL || 'http://127.0.0.1:8000',
    BACKEND_API_KEY:
      process.env.BACKEND_API_KEY ||
      process.env.API_KEY ||
      env.BACKEND_API_KEY ||
      env.API_KEY,
  };
}
