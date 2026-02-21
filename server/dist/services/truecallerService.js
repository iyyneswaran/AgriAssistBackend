"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.TruecallerService = exports.NameSource = void 0;
const truecallerjs_1 = __importDefault(require("truecallerjs"));
var NameSource;
(function (NameSource) {
    NameSource["MANUAL"] = "MANUAL";
    NameSource["TRUECALLER"] = "TRUECALLER";
})(NameSource || (exports.NameSource = NameSource = {}));
class TruecallerService {
    /**
     * Fetches a profile from Truecaller using truecallerjs.
     * Requires TRUECALLER_INSTALL_ID in .env.
     */
    static async fetchProfile(phoneNumber) {
        const installId = process.env.TRUECALLER_INSTALL_ID;
        if (!installId) {
            console.warn('[TRUECALLER] Missing TRUECALLER_INSTALL_ID. Skipping lookup.');
            return null;
        }
        console.log(`[TRUECALLER] Fetching profile for ${phoneNumber}`);
        try {
            // truecallerjs expects phone number and country code separately or as one
            // We'll try to extract country code from E.164 (e.g., +919876543210 -> countryCode: 'IN')
            // For simplicity in this demo, we'll pass the full number and let the lib handle it if possible,
            // or default to IN if it's a common case for the user.
            const searchData = {
                number: phoneNumber,
                countryCode: "IN", // Typical default, can be improved with a mapper
                installationId: installId,
            };
            const response = await truecallerjs_1.default.searchData(searchData);
            const data = response.json();
            if (data && data.data && data.data[0] && data.data[0].name) {
                return {
                    name: data.data[0].name,
                    source: NameSource.TRUECALLER
                };
            }
        }
        catch (error) {
            console.error(`[TRUECALLER] Lookup failed: ${error.message}`);
        }
        return null;
    }
}
exports.TruecallerService = TruecallerService;
//# sourceMappingURL=truecallerService.js.map