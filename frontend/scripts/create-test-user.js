const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

async function createTestUser() {
  // Set DATABASE_URL directly for this script
  process.env.DATABASE_URL = "file:C:/Ganger/Ganger/Ganger/frontend/prisma/dev.db";
  
  const prisma = new PrismaClient();
  
  try {
    // Check if test user already exists
    const existing = await prisma.user.findUnique({
      where: { email: 'test@example.com' }
    });
    
    if (existing) {
      console.log('Test user already exists:', existing.email);
      return;
    }
    
    // Create test user
    const passwordHash = await bcrypt.hash('password123', 12);
    
    const user = await prisma.user.create({
      data: {
        email: 'test@example.com',
        username: 'testuser',
        passwordHash: passwordHash
      }
    });
    
    console.log('Test user created successfully:');
    console.log('Email:', user.email);
    console.log('Username:', user.username);
    console.log('ID:', user.id);
    
  } catch (error) {
    console.error('Error creating test user:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createTestUser();
