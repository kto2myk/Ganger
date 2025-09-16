import { PrismaClient } from '@prisma/client';
import path from 'path';

// Prevent multiple instances in dev (Next.js hot reload)
const globalForPrisma = global as unknown as { prisma?: PrismaClient; __prismaEnvLogged?: boolean };

// Fallback: ensure DATABASE_URL exists (development resilience)
if (!process.env.DATABASE_URL) {
	const abs = path.join(process.cwd(), 'prisma', 'dev.db').replace(/\\/g, '/');
	process.env.DATABASE_URL = 'file:' + abs;
	console.warn('[prisma] DATABASE_URL missing. Applied absolute fallback', process.env.DATABASE_URL);
}

if (!globalForPrisma.__prismaEnvLogged) {
	const dbUrl = process.env.DATABASE_URL!;
	console.log('[prisma] Using DATABASE_URL:', dbUrl.startsWith('file:') ? dbUrl : dbUrl.slice(0, 60) + '...');
	globalForPrisma.__prismaEnvLogged = true;
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient({ log: ['warn', 'error'] });

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
