export declare enum NameSource {
    MANUAL = "MANUAL",
    TRUECALLER = "TRUECALLER"
}
export interface TruecallerProfile {
    name: string;
    source: NameSource;
}
export declare class TruecallerService {
    /**
     * Fetches a profile from Truecaller using truecallerjs.
     * Requires TRUECALLER_INSTALL_ID in .env.
     */
    static fetchProfile(phoneNumber: string): Promise<TruecallerProfile | null>;
}
//# sourceMappingURL=truecallerService.d.ts.map