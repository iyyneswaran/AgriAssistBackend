import * as dotenv from 'dotenv';
import * as path from 'path';
dotenv.config({ path: path.resolve(__dirname, '.env') });
import { db } from './src/db';

async function main() {
    // =============================
    // 1. Seed reference crops
    // =============================
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
    console.log('✅ Crops seeded.');

    // =============================
    // 2. Seed sample farm data for user 9042524161
    // =============================
    const PHONE_NUMBER = '9042524161';

    let user = await db.user.findUnique({
        where: { phoneNumber: PHONE_NUMBER },
    });

    if (!user) {
        console.log(`⚠️  User with phone ${PHONE_NUMBER} not found. Creating user...`);
        user = await db.user.create({
            data: {
                phoneNumber: PHONE_NUMBER,
                name: 'Test Farmer',
                role: 'FARMER',
                interface: 'SOFTWARE',
            }
        });
    }

    console.log(`👤 Found user: ${user.name || user.id} (${user.phoneNumber})`);

    // Get or create Farmer record
    let farmer = await db.farmer.findUnique({
        where: { userId: user.id },
    });

    if (!farmer) {
        farmer = await db.farmer.create({
            data: {
                userId: user.id,
                preferredLanguage: 'en',
                notificationPref: 'PUSH',
            },
        });
        console.log('✅ Farmer record created.');
    } else {
        console.log('✅ Farmer record already exists.');
    }

    // Corner coordinates (grandma's real farm!)
    const corners = [
        { lat: 11.100596, lng: 79.813005 },
        { lat: 11.100555, lng: 79.812620 },
        { lat: 11.101201, lng: 79.812964 },
        { lat: 11.101185, lng: 79.812616 },
    ];

    // Center point (average of corners)
    const centerLat = corners.reduce((s, c) => s + c.lat, 0) / corners.length;
    const centerLng = corners.reduce((s, c) => s + c.lng, 0) / corners.length;

    // Auto-calculate area using Shoelace formula
    const toRad = (d: number) => (d * Math.PI) / 180;
    const R = 6371000; // Earth radius in meters
    const refLat = corners[0]!.lat;
    const refLng = corners[0]!.lng;
    const points = corners.map((c) => ({
        x: (c.lng - refLng) * toRad(1) * R * Math.cos(toRad(refLat)),
        y: (c.lat - refLat) * toRad(1) * R,
    }));
    let areaSqM = 0;
    for (let i = 0; i < points.length; i++) {
        const j = (i + 1) % points.length;
        areaSqM += points[i]!.x * points[j]!.y;
        areaSqM -= points[j]!.x * points[i]!.y;
    }
    areaSqM = Math.abs(areaSqM) / 2;
    const areaAcres = Math.round((areaSqM / 4046.86) * 10000) / 10000; // ~0.3288 acres

    console.log(`📐 Computed area: ${areaSqM.toFixed(2)} sq m = ${areaAcres} acres`);

    // Create or update Land
    const existingLand = await db.land.findUnique({
        where: { farmerId: farmer.id },
    });

    let land;
    if (existingLand) {
        land = await db.land.update({
            where: { id: existingLand.id },
            data: {
                name: "Grandma's Farm",
                totalArea: areaAcres,
                soilType: 'Alluvial',
                latitude: centerLat,
                longitude: centerLng,
                district: 'Nagapattinam',
                state: 'Tamil Nadu',
                corners: corners,
                plantedCropManual: 'Paddy',
            },
        });
        console.log('✅ Land updated.');
    } else {
        land = await db.land.create({
            data: {
                farmerId: farmer.id,
                name: "Grandma's Farm",
                totalArea: areaAcres,
                soilType: 'Alluvial',
                latitude: centerLat,
                longitude: centerLng,
                district: 'Nagapattinam',
                state: 'Tamil Nadu',
                corners: corners,
                plantedCropManual: 'Paddy',
            },
        });
        console.log('✅ Land created.');
    }

    // Create or find field
    let field = await db.field.findFirst({
        where: { landId: land.id },
    });

    if (!field) {
        field = await db.field.create({
            data: {
                landId: land.id,
                name: "Grandma's Farm",
                area: areaAcres,
            },
        });
        console.log('✅ Field created.');
    } else {
        await db.field.update({
            where: { id: field.id },
            data: { area: areaAcres },
        });
        console.log('✅ Field updated.');
    }

    // Assign Paddy crop
    const paddyCrop = await db.crop.findUnique({ where: { name: 'Paddy' } });
    if (paddyCrop) {
        const existingAssignment = await db.cropAssignment.findFirst({
            where: { fieldId: field.id, status: 'ACTIVE' },
        });

        if (!existingAssignment) {
            await db.cropAssignment.create({
                data: {
                    fieldId: field.id,
                    cropId: paddyCrop.id,
                    sowingDate: new Date('2026-02-01'),
                    status: 'ACTIVE',
                },
            });
            console.log('✅ Paddy crop assigned.');
        } else {
            // Update existing assignment to Paddy
            await db.cropAssignment.update({
                where: { id: existingAssignment.id },
                data: { cropId: paddyCrop.id },
            });
            console.log('✅ Crop assignment updated to Paddy.');
        }
    }

    console.log('\n🎉 Seed completed successfully!');
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await db.$disconnect();
    });
