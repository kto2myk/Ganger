const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

async function createTestUser() {
  // Set DATABASE_URL directly for this script
  process.env.DATABASE_URL = "file:C:/Ganger/Ganger/Ganger/frontend/prisma/dev.db";
  
  const prisma = new PrismaClient();
  
  try {
    // Create multiple test users
    const testUsers = [
      { email: 'test@example.com', username: 'testuser', password: 'password123' },
      { email: 'example@example.com', username: 'exampleuser', password: 'aaaaaa' },
    ];
    
    for (const userData of testUsers) {
      const existing = await prisma.user.findUnique({
        where: { email: userData.email }
      });
      
      if (existing) {
        console.log('User already exists:', existing.email);
        continue;
      }
      
      const passwordHash = await bcrypt.hash(userData.password, 12);
      
      const user = await prisma.user.create({
        data: {
          email: userData.email,
          username: userData.username,
          passwordHash: passwordHash
        }
      });
      
      console.log('Test user created successfully:');
      console.log('Email:', user.email);
      console.log('Username:', user.username);
      console.log('Password:', userData.password);
      console.log('ID:', user.id);
      console.log('---');
    }
    
  } catch (error) {
    console.error('Error creating test user:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createTestUser();
