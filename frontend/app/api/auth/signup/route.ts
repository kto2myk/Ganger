import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '../../../../lib/prisma';
import { z } from 'zod';
import bcrypt from 'bcryptjs';

const schema = z.object({
  email: z.string().email(),
  username: z.string().min(3).max(32),
  password: z.string().min(6)
});

export async function POST(req: NextRequest) {
  try {
    const data = await req.json();
    const parsed = schema.parse(data);
    const exists = await prisma.user.findFirst({ where: { OR: [ { email: parsed.email }, { username: parsed.username } ] }});
    if (exists) return NextResponse.json({ error: 'User already exists' }, { status: 409 });
    const hash = await bcrypt.hash(parsed.password, 10);
    const user = await prisma.user.create({ data: { email: parsed.email, username: parsed.username, passwordHash: hash } });
    return NextResponse.json({ id: user.id, email: user.email, username: user.username }, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 400 });
  }
}