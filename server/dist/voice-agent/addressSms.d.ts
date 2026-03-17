interface StoredAddress {
    address: string;
    receivedAt: Date;
}
/** Returns true if this phone number has a pending address request. */
export declare function hasPendingAddressRequest(phoneNumber: string): boolean;
/**
 * Handle an inbound SMS that is a reply to an address request.
 * Stores the address, clears the pending flag, and returns an
 * acknowledgement message to send back to the user.
 */
export declare function handleAddressReply(phoneNumber: string, body: string): string;
/** Retrieve the stored address for a phone number (if any). */
export declare function getStoredAddress(phoneNumber: string): StoredAddress | undefined;
export declare function requestAddress(to: string): Promise<void>;
declare const addressSmsRouter: import("express-serve-static-core").Router;
export default addressSmsRouter;
//# sourceMappingURL=addressSms.d.ts.map