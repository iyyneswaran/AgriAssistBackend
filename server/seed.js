const { PrismaClient } = require('./src/generated/prisma');
const prisma = new PrismaClient();

async function main() {
    const crops = [
        { name: 'Cotton', growthDays: 150 },
        { name: 'Paddy', growthDays: 120 },
        { name: 'Wheat', growthDays: 130 },
        { name: 'Maize', growthDays: 100 },
        { name: 'Sugarcane', growthDays: 300 }
    ];

    for (const crop of crops) {
        await prisma.crop.upsert({
            where: { name: crop.name },
            update: {},
            create: crop,
        });
    }
    console.log('Seed completed!');
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });
