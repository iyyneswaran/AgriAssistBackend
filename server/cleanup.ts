import * as dotenv from 'dotenv';
import * as path from 'path';
dotenv.config({ path: path.resolve(__dirname, '.env') });
import { db } from './src/db';

async function main() {
    // Get all fields grouped by name to find duplicates
    const allFields = await db.field.findMany({
        include: { crops: true },
        orderBy: { name: 'asc' }
    });

    console.log(`Total fields found: ${allFields.length}`);

    // Group fields by name
    const grouped: Record<string, typeof allFields> = {};
    for (const f of allFields) {
        if (!grouped[f.name]) grouped[f.name] = [];
        grouped[f.name]!.push(f);
    }

    // For each group with duplicates, keep the first and delete the rest
    for (const [name, fields] of Object.entries(grouped)) {
        if (fields.length > 1) {
            console.log(`Found ${fields.length} duplicates for "${name}". Keeping first, deleting rest.`);
            const toDelete = fields.slice(1);
            for (const dup of toDelete) {
                // First delete crop assignments for this field
                await db.cropAssignment.deleteMany({ where: { fieldId: dup.id } });
                await db.field.delete({ where: { id: dup.id } });
                console.log(`  Deleted field ${dup.id}`);
            }
        }
    }

    const remaining = await db.field.findMany();
    console.log(`Fields remaining after cleanup: ${remaining.length}`);
}

main()
    .catch(e => { console.error(e); process.exit(1); })
    .finally(() => db.$disconnect());
