/**
 * Area Conversion Utility
 * Converts different land measurement units to Hectares (the standard DB unit).
 */
export declare const UNIT_CONVERSION: {
    HECTARE: number;
    ACRE: number;
    GROUND: number;
    CENT: number;
};
export type AreaUnit = keyof typeof UNIT_CONVERSION;
/**
 * Converts value from specified unit to Hectares
 * @param value The numerical area value
 * @param unit The unit of measurement (ACRE, GROUND, CENT, HECTARE)
 * @returns value in Hectares, rounded to 4 decimal places
 */
export declare const convertToHectares: (value: number, unit: AreaUnit) => number;
//# sourceMappingURL=areaConverter.d.ts.map