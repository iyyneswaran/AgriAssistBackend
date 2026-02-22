import * as dotenv from 'dotenv';
import * as path from 'path';
dotenv.config({ path: path.resolve(__dirname, '.env') });
import { db } from './src/db';

async function main() {
    const crops = [
        { name: 'Cotton', growthDays: 150 },
        { name: 'Paddy', growthDays: 120 },
        { name: 'Wheat', growthDays: 130 },
        { name: 'Maize', growthDays: 100 },
        { name: 'Sugarcane', growthDays: 300 }
    ];

    for (const crop of crops) {
        await db.crop.upsert({
            where: { name: crop.name },
            update: {},
            create: crop,
        });
    }
    console.log('Seed completed successfully!');
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await db.$disconnect();
    });
