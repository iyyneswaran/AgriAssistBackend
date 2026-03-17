"use strict";
/**
 * Area Conversion Utility
 * Converts different land measurement units to Hectares (the standard DB unit).
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.convertToHectares = exports.UNIT_CONVERSION = void 0;
exports.UNIT_CONVERSION = {
    HECTARE: 1.0,
    ACRE: 0.4047,
    GROUND: 0.0223,
    CENT: 0.004047
};
/**
 * Converts value from specified unit to Hectares
 * @param value The numerical area value
 * @param unit The unit of measurement (ACRE, GROUND, CENT, HECTARE)
 * @returns value in Hectares, rounded to 4 decimal places
 */
const convertToHectares = (value, unit) => {
    const conversionFactor = exports.UNIT_CONVERSION[unit] || 1.0;
    const hectares = value * conversionFactor;
    return Math.round(hectares * 10000) / 10000;
};
exports.convertToHectares = convertToHectares;
//# sourceMappingURL=areaConverter.js.map